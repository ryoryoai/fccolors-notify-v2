from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .config import env_name
from .models import ScheduleEvent

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "Asia/Tokyo"


class CalendarSync:
    def __init__(self, config: dict[str, Any], dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        credentials_text = os.environ.get(
            env_name(config, "google_service_account_key", "GOOGLE_SERVICE_ACCOUNT_KEY"),
            "",
        )
        self.service = None
        if credentials_text:
            key_data = json.loads(base64.b64decode(credentials_text))
            creds = service_account.Credentials.from_service_account_info(key_data, scopes=SCOPES)
            self.service = build("calendar", "v3", credentials=creds)

    def sync_events(self, calendar_id: str, events: list[ScheduleEvent]) -> int:
        if not calendar_id or not self.service:
            return 0
        count = 0
        for event in events:
            body = _calendar_body(event)
            if self.dry_run:
                logger.info("[DRY RUN] Calendar -> %s %s", calendar_id, body["summary"])
                count += 1
                continue
            self.service.events().insert(calendarId=calendar_id, body=body).execute()
            count += 1
        return count


def _calendar_body(event: ScheduleEvent) -> dict[str, Any]:
    summary = f"FC COLORS {event.activity or event.team}".strip()
    description = "\n".join(
        [
            f"source: {event.source_title}",
            f"team: {event.team}",
            f"notes: {event.notes}",
            f"grades: {', '.join(event.grade_labels)}",
        ]
    )
    if event.time_text and "-" in event.time_text:
        start_text, end_text = event.time_text.split("-", 1)
        return {
            "summary": summary,
            "location": event.location,
            "description": description,
            "start": {"dateTime": f"2026-{_mmdd(event.date)}T{start_text}:00", "timeZone": TIMEZONE},
            "end": {"dateTime": f"2026-{_mmdd(event.date)}T{end_text}:00", "timeZone": TIMEZONE},
        }
    date_value = f"2026-{_mmdd(event.date)}"
    next_day = (datetime.strptime(date_value, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "summary": summary,
        "location": event.location,
        "description": description,
        "start": {"date": date_value},
        "end": {"date": next_day},
    }


def _mmdd(value: str) -> str:
    month, day = value.split("/", 1)
    return f"{int(month):02d}-{int(day):02d}"
