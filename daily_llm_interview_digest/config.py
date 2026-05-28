from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    config.setdefault("output_dir", "outputs")
    config.setdefault("max_sources", 18)
    config.setdefault("model", "gpt-4.1-mini")
    config.setdefault("search", {})
    config["search"].setdefault("queries", [])
    config["search"].setdefault("trusted_domains", [])
    return config

