from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path = "config.yml") -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        path = Path("config.example.yml")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def env_name(config: dict[str, Any], key: str, default: str) -> str:
    env_cfg = config.get("env", {}) if config else {}
    value = env_cfg.get(key)
    return str(value).strip() if value else default
