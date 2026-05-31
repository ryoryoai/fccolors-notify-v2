from fccolors_notify_v2.ai_fallback import events_from_payload
from fccolors_notify_v2.models import SourceArticle


def _article() -> SourceArticle:
    return SourceArticle(
        category="weekend",
        url="http://example.com/post-9",
        title="3月休日予定",
        content_html="",
        content_text="",
        content_hash="hash",
    )


def test_null_grade_labels_does_not_crash() -> None:
    # Gemini frequently emits ``null`` for "no value"; this must not raise.
    payload = [{"date": "3/15", "grade_labels": None}]
    events = events_from_payload(_article(), payload)
    assert len(events) == 1
    assert events[0].grade_labels == []
    assert events[0].date == "3/15"


def test_null_scalar_fields_become_empty_strings() -> None:
    payload = [{"date": None, "location": None, "team": None, "grade_labels": ["1年", None]}]
    events = events_from_payload(_article(), payload)
    assert len(events) == 1
    event = events[0]
    assert event.date == ""
    assert event.location == ""
    assert event.team == "全員"
    assert event.grade_labels == ["1年"]


def test_non_list_grade_labels_is_wrapped() -> None:
    payload = [{"date": "3/15", "grade_labels": "1年"}]
    events = events_from_payload(_article(), payload)
    assert events[0].grade_labels == ["1年"]


def test_non_dict_items_are_skipped() -> None:
    payload = ["just a string", None, {"date": "3/15"}]
    events = events_from_payload(_article(), payload)
    assert len(events) == 1
    assert events[0].date == "3/15"


def test_non_list_payload_yields_no_events() -> None:
    assert events_from_payload(_article(), {"date": "3/15"}) == []
    assert events_from_payload(_article(), None) == []
