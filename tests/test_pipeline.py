from fccolors_notify_v2.models import SourceArticle
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


def test_failing_article_does_not_abort_run(monkeypatch, tmp_path) -> None:
    config = {
        "wordpress": {"categories": {"weekend": "http://example.com/hd"}},
        "state": {"path": str(tmp_path / "state.db")},
        "grades": {},
        "ai": {"enabled": False},
    }

    def fake_fetch(category: str, url: str):
        return [
            SourceArticle("weekend", "http://example.com/post-1", "bad", "", "x", "h1"),
            SourceArticle("weekend", "http://example.com/post-2", "good", "", "y", "h2"),
        ]

    def fake_parse(article):
        if article.url.endswith("post-1"):
            raise AttributeError("'NoneType' object has no attribute 'replace'")
        return [], []

    monkeypatch.setattr(pipeline, "fetch_category_articles", fake_fetch)
    monkeypatch.setattr(pipeline, "parse_article", fake_parse)

    # Must not raise even though the first article blows up.
    results = run_pipeline(config, dry_run=True)

    assert len(results) == 1
    assert results[0].soft_errors  # the failing article is recorded
    assert any("bad" in err for err in results[0].soft_errors)
