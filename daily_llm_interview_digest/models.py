from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    uncertain: bool = False


@dataclass(frozen=True)
class SourceDocument:
    title: str
    url: str
    text: str
    source: str
    uncertain: bool = False


@dataclass
class DigestContext:
    run_date: date
    sources: list[SourceDocument] = field(default_factory=list)
    config: dict = field(default_factory=dict)

