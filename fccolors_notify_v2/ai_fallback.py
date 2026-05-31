from __future__ import annotations

import json
import logging
import os

import requests

from .config import env_name
from .models import ScheduleEvent, SourceArticle

logger = logging.getLogger(__name__)
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def parse_unresolved_lines(
    article: SourceArticle,
    unresolved_lines: list[str],
    config: dict,
) -> list[ScheduleEvent]:
    if not unresolved_lines:
        return []

    api_key = os.environ.get(env_name(config, "gemini_api_key", "GEMINI_API_KEY"), "").strip()
    if not api_key:
        return []

    prompt = (
        "FC COLORS schedule lines to JSON.\n"
        "Return a JSON array. Each item must have: "
        "date, weekday, team, location, activity, time_text, notes, grade_labels.\n"
        f"Title: {article.title}\n"
        f"Category: {article.category}\n"
        "Lines:\n"
        + "\n".join(f"- {line}" for line in unresolved_lines[:20])
    )
    try:
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0}},
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        payload = json.loads(text)
    except Exception as exc:
        logger.warning("AI fallback failed for %s: %s", article.title, exc)
        return []

    return events_from_payload(article, payload)


def _as_text(value: object, default: str = "") -> str:
    """Coerce an arbitrary JSON value to a clean string, treating null as the default."""
    if value is None:
        return default
    return str(value)


def events_from_payload(article: SourceArticle, payload: object) -> list[ScheduleEvent]:
    """Build events from a parsed Gemini payload.

    The model output is untrusted: fields may be missing, ``null``, or the wrong
    type. Coerce everything defensively so a stray ``null`` never crashes the run.
    """
    events: list[ScheduleEvent] = []
    for item in payload if isinstance(payload, list) else []:
        if not isinstance(item, dict):
            logger.warning("Skipping non-object AI item for %s: %r", article.title, item)
            continue
        raw_grades = item.get("grade_labels") or []
        if not isinstance(raw_grades, list):
            raw_grades = [raw_grades]
        grade_labels = [_as_text(v) for v in raw_grades if v is not None]
        events.append(
            ScheduleEvent(
                source_url=article.url,
                source_title=article.title,
                category=article.category,
                date=_as_text(item.get("date")),
                weekday=_as_text(item.get("weekday")),
                team=_as_text(item.get("team"), "全員") or "全員",
                location=_as_text(item.get("location")),
                activity=_as_text(item.get("activity")),
                time_text=_as_text(item.get("time_text")),
                notes=_as_text(item.get("notes")),
                grade_labels=grade_labels,
                parser="ai",
                confidence=0.6,
            )
        )
    return events
