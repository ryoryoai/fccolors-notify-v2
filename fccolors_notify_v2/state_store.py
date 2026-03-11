from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import ScheduleEvent, SourceArticle


SCHEMA = """
create table if not exists articles (
  url text primary key,
  category text not null,
  title text not null,
  content_hash text not null
);
create table if not exists events (
  event_key text primary key,
  source_url text not null,
  payload_json text not null
);
"""


class StateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def article_changed(self, article: SourceArticle) -> bool:
        row = self.conn.execute(
            "select content_hash from articles where url = ?",
            (article.url,),
        ).fetchone()
        if row is None:
            return True
        return str(row[0]) != article.content_hash

    def save_article(self, article: SourceArticle) -> None:
        self.conn.execute(
            "insert into articles(url, category, title, content_hash) values(?, ?, ?, ?) "
            "on conflict(url) do update set category=excluded.category, title=excluded.title, content_hash=excluded.content_hash",
            (article.url, article.category, article.title, article.content_hash),
        )
        self.conn.commit()

    def get_events_for_source(self, source_url: str) -> list[ScheduleEvent]:
        rows = self.conn.execute(
            "select payload_json from events where source_url = ?",
            (source_url,),
        ).fetchall()
        result: list[ScheduleEvent] = []
        for (payload_json,) in rows:
            payload = json.loads(payload_json)
            result.append(ScheduleEvent(**payload))
        return result

    def replace_events_for_source(self, source_url: str, events: list[ScheduleEvent]) -> None:
        self.conn.execute("delete from events where source_url = ?", (source_url,))
        for event in events:
            self.conn.execute(
                "insert into events(event_key, source_url, payload_json) values(?, ?, ?)",
                (event.event_key, source_url, json.dumps(event.__dict__, ensure_ascii=False)),
            )
        self.conn.commit()
