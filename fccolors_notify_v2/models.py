from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class SourceArticle:
    category: str
    url: str
    title: str
    content_html: str
    content_text: str
    content_hash: str


@dataclass
class ScheduleEvent:
    source_url: str
    source_title: str
    category: str
    date: str
    weekday: str
    team: str
    location: str
    activity: str
    time_text: str
    notes: str
    grade_labels: list[str] = field(default_factory=list)
    parser: str = "rules"
    confidence: float = 1.0

    @property
    def event_key(self) -> str:
        raw = "|".join(
            [
                self.date,
                self.weekday,
                self.team,
                self.location,
                self.activity,
                self.time_text,
                self.notes,
                ",".join(sorted(self.grade_labels)),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class EventDiff:
    added: list[ScheduleEvent] = field(default_factory=list)
    changed: list[tuple[ScheduleEvent, ScheduleEvent]] = field(default_factory=list)
    removed: list[ScheduleEvent] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.added or self.changed or self.removed)


@dataclass
class RunResult:
    category: str
    article_count: int = 0
    parsed_events: int = 0
    notifications_sent: int = 0
    calendar_writes: int = 0
    soft_errors: list[str] = field(default_factory=list)
