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


def test_parse_weekday_spring_block_article() -> None:
    article = SourceArticle(
        category="weekday",
        url="http://example.com/post-4",
        title="3月平日予定",
        content_html="",
        content_text=(
            "◎金曜日コース→園児.1.2.3年生\n"
            "6日 北野G\n"
            "【春休み練習】\n"
            "24日(火)新1年生,園児練習(北野G17:00開門 17:30〜19:00)\n"
            "26日(木)新4,5,6年練習(戸吹G)\n"
        ),
        content_hash="hash",
    )
    events, unresolved = parse_article(article)
    assert unresolved == []
    spring = [e for e in events if e.date == "3/24"][0]
    assert spring.weekday == "火"
    assert spring.time_text == "17:30-19:00"
    assert spring.location == "北野グラウンド"
    assert spring.grade_labels == ["園児"]


def test_parse_weekend_block_with_multiple_team_entries() -> None:
    article = SourceArticle(
        category="weekend",
        url="http://example.com/post-5",
        title="3月休日予定",
        content_html="",
        content_text=(
            "◎15(日)\n"
            "・5年生 1紅白戦8:30-10:30 川町G / 2OFF\n"
            "・1年生 1小山FC招待 ※ / 2練習9:30-11:30 プレイパーク ※\n"
        ),
        content_hash="hash",
    )
    events, unresolved = parse_article(article)
    assert unresolved == []
    assert len(events) == 4

    first = events[0]
    assert first.grade_labels == ["5年"]
    assert first.team == "1"
    assert first.activity == "紅白戦"
    assert first.time_text == "8:30-10:30"
    assert first.location == "川町G"

    second = events[1]
    assert second.grade_labels == ["5年"]
    assert second.team == "2"
    assert second.activity == "OFF"

    third = events[2]
    assert third.grade_labels == ["1年"]
    assert third.team == "1"
    assert "小山FC招待" in third.activity

    fourth = events[3]
    assert fourth.grade_labels == ["1年"]
    assert fourth.team == "2"
    assert fourth.activity == "練習"
    assert fourth.time_text == "9:30-11:30"
