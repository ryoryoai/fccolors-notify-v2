from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from .config import load_config
from .pipeline import run_pipeline


def main() -> int:
    load_dotenv()
    logging.basicConfig(
        level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="FC COLORS Notify V2")
    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--category", choices=["weekday", "weekend"])
    parser.add_argument("--reparse-all", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    run_pipeline(
        config,
        dry_run=args.dry_run,
        category=args.category,
        reparse_all=args.reparse_all,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
