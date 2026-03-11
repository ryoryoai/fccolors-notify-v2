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

    events: list[ScheduleEvent] = []
    for item in payload if isinstance(payload, list) else []:
        events.append(
            ScheduleEvent(
                source_url=article.url,
                source_title=article.title,
                category=article.category,
                date=str(item.get("date", "")),
                weekday=str(item.get("weekday", "")),
                team=str(item.get("team", "全員") or "全員"),
                location=str(item.get("location", "")),
                activity=str(item.get("activity", "")),
                time_text=str(item.get("time_text", "")),
                notes=str(item.get("notes", "")),
                grade_labels=[str(v) for v in item.get("grade_labels", [])],
                parser="ai",
                confidence=0.6,
            )
        )
    return events
