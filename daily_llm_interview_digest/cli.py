from __future__ import annotations

import argparse
from datetime import date

from .config import load_config
from .digest import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Daily LLM Interview Digest.")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config.")
    parser.add_argument("--date", default=None, help="Run date, format YYYY-MM-DD.")
    args = parser.parse_args()

    config = load_config(args.config)
    run_date = date.fromisoformat(args.date) if args.date else None
    output_path = run(config=config, run_date=run_date)
    print(f"Digest generated: {output_path}")

