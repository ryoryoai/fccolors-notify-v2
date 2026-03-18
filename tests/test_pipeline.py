from fccolors_notify_v2.pipeline import run_pipeline
import fccolors_notify_v2.pipeline as pipeline
from fccolors_notify_v2.wordpress import TransientFetchError


def test_transient_category_fetch_does_not_abort_pipeline(monkeypatch, tmp_path) -> None:
    config = {
        "wordpress": {"categories": {"weekday": "http://example.com/wd", "weekend": "http://example.com/hd"}},
        "state": {"path": str(tmp_path / "state.db")},
        "grades": {},
        "ai": {"enabled": False},
    }

    def fake_fetch(category: str, url: str):
        if category == "weekday":
            raise TransientFetchError("500 server error")
        return []

    monkeypatch.setattr(pipeline, "fetch_category_articles", fake_fetch)

    results = run_pipeline(config, dry_run=True)

    assert len(results) == 2
    weekday = [result for result in results if result.category == "weekday"][0]
    weekend = [result for result in results if result.category == "weekend"][0]
    assert weekday.soft_errors
    assert weekend.soft_errors == []
