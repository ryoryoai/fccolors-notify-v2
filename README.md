# FC COLORS Notify V2

WordPress にテキストで掲載される FC COLORS の予定を構造化し、Google Calendar と LINE に反映する V2 実装です。

V1 との違い:

- 予定差分ベースで通知
- ルールベース parser を主軸にし、AI は補助
- state は Git 管理の JSON ではなく SQLite
- 配信と解析を分離

## Structure

```text
fccolors-notify-v2/
├── fccolors_notify_v2/
│   ├── ai_fallback.py
│   ├── calendar_sync.py
│   ├── cli.py
│   ├── config.py
│   ├── diffing.py
│   ├── line_notify.py
│   ├── models.py
│   ├── normalize.py
│   ├── pipeline.py
│   ├── rule_parser.py
│   ├── state_store.py
│   └── wordpress.py
├── tests/
├── config.example.yml
└── requirements.txt
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp config.example.yml config.yml
python -m fccolors_notify_v2.cli --dry-run
```

## Commands

```bash
python -m fccolors_notify_v2.cli
python -m fccolors_notify_v2.cli --dry-run
python -m fccolors_notify_v2.cli --category weekend --dry-run
python -m fccolors_notify_v2.cli --category weekend --reparse-all --dry-run
```

## Environment variables

- `LINE_CHANNEL_TOKEN`
- `ADMIN_USER_ID`
- `GEMINI_API_KEY` (optional)
- `GOOGLE_SERVICE_ACCOUNT_KEY`
- `LINE_GROUP_2017`
- `CALENDAR_ID_2017`

## Design

1. WordPress category page から記事取得
2. 本文を整形して schedule lines を抽出
3. ルールベース parser で `ScheduleEvent` に変換
4. 解釈できなかった行だけ AI fallback
5. SQLite に保存済み event と比較
6. Google Calendar 同期
7. LINE 通知

## GitHub Actions

最初は `workflow_dispatch` と手動 dry-run で検証し、安定後に cron を有効化してください。
