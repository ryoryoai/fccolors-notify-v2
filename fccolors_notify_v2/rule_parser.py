from __future__ import annotations

import logging
import re

from .models import ScheduleEvent, SourceArticle
from .normalize import normalize_location, normalize_text, normalize_time

logger = logging.getLogger(__name__)


GRADE_TOKENS = ["園児", "1年", "2年", "3年", "4年", "5年", "6年"]
WEEKDAY_GRADE_MAP = {
    "火": ["園児", "1年", "2年", "3年"],
    "金": ["園児", "1年", "2年", "3年"],
    "水": ["4年", "5年", "6年"],
    "木": ["4年", "5年", "6年"],
}


def _extract_month(title: str, text: str) -> str:
    for source in (title, text[:200]):
        match = re.search(r"(\d{1,2})月", source or "")
        if match:
            return match.group(1)
    return ""


def _extract_grades(text: str, category: str, weekday_hint: str = "") -> list[str]:
    grades = [token for token in GRADE_TOKENS if token in text]
    if grades:
        return grades
    if category == "weekday" and weekday_hint in WEEKDAY_GRADE_MAP:
        return WEEKDAY_GRADE_MAP[weekday_hint]
    return []


def _extract_team(text: str) -> str:
    if "Aチーム" in text or "①" in text:
        return "A"
    if "Bチーム" in text or "②" in text:
        return "B"
    if "選抜" in text:
        return "選抜"
    return "全員"


def _split_rest(rest: str) -> tuple[str, str, str, str]:
    time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*[-〜～]\s*\d{1,2}(?::\d{2})?)", rest)
    time_text = normalize_time(time_match.group(1)) if time_match else ""
    if time_match:
        rest = rest.replace(time_match.group(1), " ").strip()

    parts = [part.strip() for part in re.split(r"[／/|]", rest) if part.strip()]
    location = normalize_location(parts[0]) if parts else ""
    activity = parts[1] if len(parts) >= 2 else ""
    notes = " / ".join(parts[2:]) if len(parts) >= 3 else ""
    if not activity and len(parts) == 1:
        activity = ""
    return location, activity, notes, time_text


def _parse_weekend_line(
    article: SourceArticle,
    line: str,
    default_month: str,
) -> ScheduleEvent | None:
    match = re.match(r"[◎○●]?\s*(?:(\d{1,2})/)?(\d{1,2})\s*[(（]([月火水木金土日祝])[)）]?\s*(.*)", line)
    if not match:
        return None
    month, day, weekday, rest = match.groups()
    date_value = f"{month or default_month}/{day}" if (month or default_month) else day
    location, activity, notes, time_text = _split_rest(rest)
    return ScheduleEvent(
        source_url=article.url,
        source_title=article.title,
        category=article.category,
        date=date_value,
        weekday=weekday,
        team=_extract_team(rest),
        location=location,
        activity=activity,
        time_text=time_text,
        notes=notes,
        grade_labels=_extract_grades(rest, article.category),
    )


def _parse_weekday_lines(article: SourceArticle, lines: list[str], default_month: str) -> list[ScheduleEvent]:
    events: list[ScheduleEvent] = []
    current_weekday = ""
    for line in lines:
        course_match = re.match(r"[◎○●]?\s*([月火水木金土日])曜日.*", line)
        if course_match:
            current_weekday = course_match.group(1)
            continue
        day_match = re.match(r"(\d{1,2})日\s*(.*)", line)
        if not day_match:
            continue
        day, rest = day_match.groups()
        location, activity, notes, time_text = _split_rest(rest)
        events.append(
            ScheduleEvent(
                source_url=article.url,
                source_title=article.title,
                category=article.category,
                date=f"{default_month}/{day}" if default_month else day,
                weekday=current_weekday,
                team=_extract_team(rest),
                location=location,
                activity=activity,
                time_text=time_text,
                notes=notes,
                grade_labels=_extract_grades(rest, article.category, current_weekday),
            )
        )
    return events


def parse_article(article: SourceArticle) -> tuple[list[ScheduleEvent], list[str]]:
    text = normalize_text(article.content_text)
    lines = [line for line in text.split("\n") if line.strip()]
    default_month = _extract_month(article.title, text)

    parsed: list[ScheduleEvent] = []
    unresolved: list[str] = []

    if article.category == "weekday":
        parsed = _parse_weekday_lines(article, lines, default_month)
    else:
        for line in lines:
            event = _parse_weekend_line(article, line, default_month)
            if event is not None:
                parsed.append(event)
            elif re.search(r"\d{1,2}", line):
                unresolved.append(line)

    filtered = [
        event
        for event in parsed
        if event.location or event.activity or event.time_text or event.grade_labels
    ]
    logger.info("Parsed %s event(s) from %s", len(filtered), article.title)
    return filtered, unresolved
