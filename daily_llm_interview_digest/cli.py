from __future__ import annotations

import argparse
from datetime import date

from .config import load_config
from .digest import run
from .notify import notify


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Daily LLM Interview Digest.")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config.")
    parser.add_argument("--date", default=None, help="Run date, format YYYY-MM-DD.")
    parser.add_argument("--notify", action="store_true", help="Send digest through configured channels.")
    args = parser.parse_args()

    config = load_config(args.config)
    run_date = date.fromisoformat(args.date) if args.date else None
    output_path = run(config=config, run_date=run_date)
    print(f"Digest generated: {output_path}")
    if args.notify:
        sent_channels = notify(output_path)
        if sent_channels:
            print(f"Notification sent: {', '.join(sent_channels)}")
        else:
            print("Notification skipped: no notification channel configured.")
