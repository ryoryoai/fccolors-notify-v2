from fccolors_notify_v2.models import SourceArticle
from fccolors_notify_v2.rule_parser import parse_article


def test_parse_weekday_article() -> None:
    article = SourceArticle(
        category="weekday",
        url="http://example.com/post-1",
        title="2月平日予定",
        content_html="",
        content_text="◎火曜日コース→園児.1.2.3年生\n13日 北野G 17:15-19:00\n",
        content_hash="hash",
    )
    events, unresolved = parse_article(article)
    assert len(events) == 1
    assert unresolved == []
    assert events[0].date == "2/13"
    assert "2年" in events[0].grade_labels


def test_parse_weekend_article() -> None:
    article = SourceArticle(
        category="weekend",
        url="http://example.com/post-2",
        title="2月休日予定",
        content_html="",
        content_text="◎3(土) 北野G / TRM / 2年 9:00-11:00\n",
        content_hash="hash",
    )
    events, _ = parse_article(article)
    assert len(events) == 1
    assert events[0].date == "2/3"
    assert events[0].location == "北野グラウンド"


def test_parse_weekend_block_article() -> None:
    article = SourceArticle(
        category="weekend",
        url="http://example.com/post-3",
        title="3月休日予定",
        content_html="",
        content_text="◎1(日)\n・2年生 練習10-12 プレイパーク\n・1年生 OFF\n",
        content_hash="hash",
    )
    events, unresolved = parse_article(article)
    assert len(events) == 2
    assert unresolved == []
    assert events[0].date == "3/1"
    assert events[0].grade_labels == ["2年"]
