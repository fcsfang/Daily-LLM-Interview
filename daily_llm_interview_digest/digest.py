from __future__ import annotations

from datetime import date
from pathlib import Path

from .history import build_learning_context, update_history_index
from .llm import generate_digest
from .models import DigestContext
from .search import collect_sources
from .validate import validate_digest


def run(config: dict, run_date: date | None = None) -> Path:
    today = run_date or date.today()
    sources = collect_sources(config)
    learning_context = build_learning_context(config, today)
    context = DigestContext(
        run_date=today,
        sources=sources,
        config=config,
        learning_context=learning_context,
    )
    digest = generate_digest(context)
    errors = validate_digest(digest)
    if errors:
        digest += "\n\n## 生成校验提示\n"
        digest += "\n".join(f"- {error}" for error in errors)

    output_dir = Path(config.get("output_dir", "outputs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{today.isoformat()}.md"
    output_path.write_text(digest, encoding="utf-8")
    update_history_index(output_path, today)
    return output_path
