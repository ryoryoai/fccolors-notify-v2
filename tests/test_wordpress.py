from fccolors_notify_v2.wordpress import is_schedule_article


def test_is_schedule_article_for_weekday() -> None:
    assert is_schedule_article("3月平日練習(R8)", "weekday") is True
    assert is_schedule_article("新4年生 大募集！", "weekday") is False


def test_is_schedule_article_for_weekend() -> None:
    assert is_schedule_article("3月休日+春休み予定(R8)", "weekend") is True
    assert is_schedule_article("【2026年度選手クラス募集】", "weekend") is False
