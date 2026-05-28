from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any


THEME_BY_WEEKDAY = {
    0: {
        "name": "RAG",
        "focus": "检索、chunk、rerank、引用、幻觉控制、RAG 评测",
    },
    1: {
        "name": "Agent",
        "focus": "tool calling、planner/executor、memory、状态管理、错误恢复",
    },
    2: {
        "name": "LoRA / SFT / PEFT",
        "focus": "LoRA、QLoRA、SFT 数据构造、过拟合、adapter 部署",
    },
    3: {
        "name": "模型评测",
        "focus": "离线评测、LLM-as-judge、RAG eval、Agent eval、bad case 分析",
    },
    4: {
        "name": "模型部署 / 推理优化",
        "focus": "量化、KV cache、batch、吞吐、延迟、成本、服务稳定性",
    },
    5: {
        "name": "LLM 应用工程",
        "focus": "Prompt、工作流编排、权限、安全、日志、可观测性",
    },
    6: {
        "name": "综合复盘 / 模拟面试",
        "focus": "跨模块综合题、项目讲述、追问串联、薄弱点复盘",
    },
}

INDEX_FILENAME = "index.json"


def build_learning_context(config: dict, run_date: date) -> dict[str, Any]:
    output_dir = Path(config.get("output_dir", "outputs"))
    index = load_history_index(output_dir)
    recent_entries = _recent_entries(index, days=int(config.get("history", {}).get("lookback_days", 7)))
    theme = theme_for_date(run_date)
    return {
        "theme": theme,
        "recent_questions": _unique_flatten(recent_entries, "questions")[:20],
        "recent_keywords": _unique_flatten(recent_entries, "keywords")[:30],
        "recent_tasks": _unique_flatten(recent_entries, "tasks")[:10],
        "blog_mix": config.get("content_policy", {}).get(
            "blog_mix",
            ["工程实践", "理论/论文", "岗位 JD 或面经"],
        ),
    }


def load_history_index(output_dir: Path) -> dict[str, Any]:
    index_path = output_dir / INDEX_FILENAME
    if not index_path.exists():
        return {"entries": []}
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"entries": []}


def update_history_index(output_path: Path, run_date: date) -> None:
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    index = load_history_index(output_dir)
    markdown = output_path.read_text(encoding="utf-8")
    entry = {
        "date": run_date.isoformat(),
        "file": output_path.name,
        "theme": theme_for_date(run_date)["name"],
        "questions": extract_questions(markdown),
        "keywords": extract_keywords(markdown),
        "tasks": extract_tasks(markdown),
    }

    entries = [item for item in index.get("entries", []) if item.get("date") != entry["date"]]
    entries.append(entry)
    entries.sort(key=lambda item: item.get("date", ""))
    max_entries = 60
    index["entries"] = entries[-max_entries:]
    (output_dir / INDEX_FILENAME).write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def theme_for_date(run_date: date) -> dict[str, str]:
    return THEME_BY_WEEKDAY[run_date.weekday()]


def extract_questions(markdown: str) -> list[str]:
    patterns = [
        r"^###\s*题目\s*\d+[：:]\s*(.+)$",
        r"^###\s*问题\s*\d*[：:]\s*(.+)$",
        r"^\*\*Q[：:]\*\*\s*(.+)$",
        r"^\d+\.\s*\*\*Q[：:]\*\*\s*(.+)$",
    ]
    questions: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        for pattern in patterns:
            match = re.match(pattern, stripped)
            if match:
                questions.append(_clean_text(match.group(1)))
                break
    return _unique(questions)


def extract_keywords(markdown: str) -> list[str]:
    keywords: list[str] = []
    capture_next = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if capture_next and stripped:
            keywords.extend(_split_keywords(stripped))
            capture_next = False
            continue
        if "记忆关键词" in line:
            _, _, tail = line.partition("：")
            extracted = _split_keywords(tail)
            if extracted:
                keywords.extend(extracted)
            else:
                capture_next = True
        if "复习标签" in line:
            keywords.extend(re.findall(r"#[\w\u4e00-\u9fff/-]+", line))
    return _unique([item for item in keywords if item])


def extract_tasks(markdown: str) -> list[str]:
    tasks: list[str] = []
    capture = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("### 4."):
            capture = True
            tasks.append(stripped.lstrip("# ").strip())
            continue
        if stripped.startswith(("### 大模型理论题", "### 大模型理论追问题")):
            tasks.append(stripped.lstrip("# ").strip())
            continue
        if capture and stripped.startswith("## "):
            capture = False
        elif capture and stripped.startswith("- 题目"):
            tasks.append(_clean_text(stripped.lstrip("- ")))
    return _unique(tasks)


def _recent_entries(index: dict[str, Any], days: int) -> list[dict[str, Any]]:
    entries = index.get("entries", [])
    return list(reversed(entries[-days:]))


def _unique_flatten(entries: list[dict[str, Any]], key: str) -> list[str]:
    items: list[str] = []
    for entry in entries:
        items.extend(entry.get(key, []))
    return _unique(items)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = _clean_text(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _clean_text(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("`", "")
    return re.sub(r"\s+", " ", text).strip(" -：:，,。")


def _split_keywords(text: str) -> list[str]:
    keywords = [_clean_text(item) for item in re.split(r"[、+;；]+", text)]
    return [
        item
        for item in keywords
        if item
        and item not in {"+", "###", "记忆关键词"}
        and not item.startswith("缺少字段")
        and not item.startswith("###")
    ]
