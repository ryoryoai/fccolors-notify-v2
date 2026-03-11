from __future__ import annotations

from .models import EventDiff, ScheduleEvent


def diff_events(old_events: list[ScheduleEvent], new_events: list[ScheduleEvent]) -> EventDiff:
    old_map = {event.event_key: event for event in old_events}
    new_map = {event.event_key: event for event in new_events}

    added = [new_map[key] for key in new_map.keys() - old_map.keys()]
    removed = [old_map[key] for key in old_map.keys() - new_map.keys()]
    changed: list[tuple[ScheduleEvent, ScheduleEvent]] = []
    return EventDiff(added=sorted(added, key=lambda e: (e.date, e.time_text, e.location)), changed=changed, removed=sorted(removed, key=lambda e: (e.date, e.time_text, e.location)))
