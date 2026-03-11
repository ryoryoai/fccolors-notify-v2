from __future__ import annotations

import logging
import os
from typing import Any

import requests

from .config import env_name
from .models import EventDiff, ScheduleEvent

logger = logging.getLogger(__name__)
LINE_API_URL = "https://api.line.me/v2/bot/message/push"


class LineNotifier:
    def __init__(self, config: dict[str, Any], dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.token = os.environ.get(env_name(config, "line_channel_token", "LINE_CHANNEL_TOKEN"), "")
        self.admin_id = os.environ.get(env_name(config, "admin_user_id", "ADMIN_USER_ID"), "")

    def _send(self, target: str, message: str) -> bool:
        if self.dry_run:
            logger.info("[DRY RUN] LINE -> %s: %s", target[:8], message[:120])
            return True
        response = requests.post(
            LINE_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            json={"to": target, "messages": [{"type": "text", "text": message}]},
            timeout=30,
        )
        return response.status_code == 200

    def send_error(self, message: str) -> bool:
        if not self.admin_id:
            return False
        return self._send(self.admin_id, message)

    def send_schedule_update(self, group_id: str, message: str) -> bool:
        return self._send(group_id, message)


def format_diff_message(title: str, diff: EventDiff) -> str:
    lines = [f"【FC COLORS】{title}"]
    if diff.added:
        lines.append("")
        lines.append("追加:")
        for event in diff.added:
            lines.append(_format_event(event))
    if diff.removed:
        lines.append("")
        lines.append("削除:")
        for event in diff.removed:
            lines.append(_format_event(event))
    return "\n".join(lines)


def _format_event(event: ScheduleEvent) -> str:
    bits = [event.date]
    if event.weekday:
        bits[-1] += f"({event.weekday})"
    if event.time_text:
        bits.append(event.time_text)
    if event.location:
        bits.append(event.location)
    if event.activity:
        bits.append(event.activity)
    if event.notes:
        bits.append(event.notes)
    return f"- {' / '.join(bits)}"
