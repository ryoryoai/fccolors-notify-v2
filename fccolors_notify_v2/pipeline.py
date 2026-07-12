from __future__ import annotations

import logging
import os
from datetime import datetime

from .ai_fallback import parse_unresolved_lines
from .calendar_sync import CalendarSync
from .diffing import diff_events
from .line_notify import LineNotifier, format_diff_message
from .models import RunResult
from .rule_parser import parse_article
from .state_store import StateStore
from .wordpress import PermanentFetchError, TransientFetchError, fetch_category_articles

logger = logging.getLogger(__name__)


def run_pipeline(
    config: dict,
    *,
    dry_run: bool = False,
    category: str | None = None,
    reparse_all: bool = False,
) -> list[RunResult]:
    state_path = config.get("state", {}).get("path", "data/fccolors_v2.db")
    store = StateStore(state_path)
    notifier = LineNotifier(config, dry_run=dry_run)
    calendar_sync = CalendarSync(config, dry_run=dry_run)
    results: list[RunResult] = []

    try:
        categories = config.get("wordpress", {}).get("categories", {})
        selected = {category: categories[category]} if category else categories
        for category_name, url in selected.items():
            run_result = RunResult(category=category_name)
            try:
                articles = fetch_category_articles(category_name, url)
            except TransientFetchError as exc:
                logger.warning("Transient category fetch failure for %s: %s", category_name, exc)
                run_result.soft_errors.append(f"{category_name}: {exc}")
                results.append(run_result)
                continue
            except PermanentFetchError as exc:
                logger.error("Permanent category fetch failure for %s: %s", category_name, exc)
                run_result.soft_errors.append(f"{category_name}: {exc}")
                results.append(run_result)
                continue
            run_result.article_count = len(articles)
            for article in articles:
                try:
                    if not reparse_all and not store.article_changed(article):
                        continue
                    events, unresolved = parse_article(article)
                    if unresolved and config.get("ai", {}).get("enabled", True):
                        events.extend(parse_unresolved_lines(article, unresolved, config))
                    old_events = store.get_events_for_source(article.url)
                    diff = diff_events(old_events, events)
                    if diff.has_changes():
                        _deliver_changes(config, notifier, calendar_sync, article, diff, dry_run, run_result)
                    store.save_article(article)
                    store.replace_events_for_source(article.url, events)
                    run_result.parsed_events += len(events)
                except Exception as exc:
                    # One malformed article (or AI response) must not abort the whole
                    # scheduled run and black out notifications for every other post.
                    logger.exception("Failed to process article %s", article.url)
                    run_result.soft_errors.append(f"{article.title}: {exc}")
                    notifier.send_error(_format_error(f"記事処理中 ({article.title})", exc))
            results.append(run_result)
    except Exception as exc:
        logger.exception("Pipeline run failed")
        notifier.send_error(_format_error("スケジュール取得中", exc))
        raise
    finally:
        store.close()
    return results


def _format_error(stage: str, exc: Exception) -> str:
    return (
        "【FC COLORS V2】⚠️ エラー発生\n\n"
        f"{stage}にエラーが発生しました。\n\n"
        f"詳細: {type(exc).__name__}: {exc}\n"
        f"時刻: {datetime.now():%Y-%m-%d %H:%M:%S}"
    )


def _deliver_changes(config: dict, notifier: LineNotifier, calendar_sync: CalendarSync, article, diff, dry_run: bool, result: RunResult) -> None:
    enabled_grades = config.get("grades", {})
    for birth_year, grade in enabled_grades.items():
        if not grade.get("enabled", True):
            continue
        group_env = grade.get("line_group_env")
        calendar_env = grade.get("calendar_id_env")
        group_id = os.environ.get(group_env, "") if group_env else ""
        calendar_id = os.environ.get(calendar_env, "") if calendar_env else ""
        grade_label = str(_grade_from_birth_year(int(birth_year)))
        grade_events = [
            event for event in diff.added if (not event.grade_labels or grade_label in event.grade_labels)
        ]
        if grade_events and group_id:
            sent = notifier.send_schedule_update(group_id, format_diff_message(article.title, diff_events([], grade_events)))
            if sent:
                result.notifications_sent += 1
            result.calendar_writes += calendar_sync.sync_events(calendar_id, grade_events)


def _grade_from_birth_year(year: int) -> str:
    now = datetime.now()
    fiscal_year = now.year if now.month >= 4 else now.year - 1
    return f"{max(1, min(6, fiscal_year - year - 6))}年"
