from fccolors_notify_v2.diffing import diff_events
from fccolors_notify_v2.models import ScheduleEvent


def _event(date: str) -> ScheduleEvent:
    return ScheduleEvent(
        source_url="http://example.com/post-1",
        source_title="title",
        category="weekend",
        date=date,
        weekday="土",
        team="全員",
        location="北野グラウンド",
        activity="TRM",
        time_text="9:00-11:00",
        notes="",
        grade_labels=["2年"],
    )


def test_diff_added_removed() -> None:
    diff = diff_events([_event("2/1")], [_event("2/2")])
    assert len(diff.added) == 1
    assert len(diff.removed) == 1
