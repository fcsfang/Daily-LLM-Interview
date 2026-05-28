from __future__ import annotations

import os
import re
from html import unescape
from urllib.parse import parse_qs, quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from .models import SearchResult, SourceDocument

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
TIMEOUT = 15


def collect_sources(config: dict) -> list[SourceDocument]:
    queries = config.get("search", {}).get("queries", [])
    trusted_domains = set(config.get("search", {}).get("trusted_domains", []))
    max_sources = int(config.get("max_sources", 18))

    results: list[SearchResult] = []
    for query in queries:
        results.extend(search_web(query, trusted_domains))

    deduped_results = _dedupe_results(results)
    documents: list[SourceDocument] = []
    for result in deduped_results[: max_sources * 2]:
        document = fetch_document(result, trusted_domains)
        if document and len(document.text) >= 120:
            documents.append(document)
        if len(documents) >= max_sources:
            break

    return documents


def search_web(query: str, trusted_domains: set[str]) -> list[SearchResult]:
    if os.getenv("TAVILY_API_KEY"):
        return _search_tavily(query, trusted_domains)
    if os.getenv("BRAVE_SEARCH_API_KEY"):
        return _search_brave(query, trusted_domains)
    return _search_duckduckgo(query, trusted_domains)


def fetch_document(result: SearchResult, trusted_domains: set[str]) -> SourceDocument | None:
    try:
        response = requests.get(
            result.url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        return SourceDocument(
            title=result.title,
            url=result.url,
            text=result.snippet,
            source=result.source,
            uncertain=True,
        )

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    title = _clean_text(soup.title.get_text(" ")) if soup.title else result.title
    paragraphs = [_clean_text(node.get_text(" ")) for node in soup.find_all(["p", "li", "h1", "h2", "h3"])]
    text = "\n".join(part for part in paragraphs if len(part) > 20)
    if not text:
        text = result.snippet

    host = _host(result.url)
    uncertain = result.uncertain or not _is_trusted(host, trusted_domains)
    return SourceDocument(
        title=title[:180] or result.title,
        url=result.url,
        text=text[:6000],
        source=result.source,
        uncertain=uncertain,
    )


def _search_tavily(query: str, trusted_domains: set[str]) -> list[SearchResult]:
    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": os.environ["TAVILY_API_KEY"],
            "query": query,
            "search_depth": "advanced",
            "max_results": 8,
            "include_answer": False,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    items = response.json().get("results", [])
    return [
        SearchResult(
            title=item.get("title", "").strip(),
            url=item.get("url", "").strip(),
            snippet=item.get("content", "").strip(),
            source="tavily",
            uncertain=not _is_trusted(_host(item.get("url", "")), trusted_domains),
        )
        for item in items
        if item.get("url")
    ]


def _search_brave(query: str, trusted_domains: set[str]) -> list[SearchResult]:
    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": 8},
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": os.environ["BRAVE_SEARCH_API_KEY"],
            "User-Agent": USER_AGENT,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    items = response.json().get("web", {}).get("results", [])
    return [
        SearchResult(
            title=item.get("title", "").strip(),
            url=item.get("url", "").strip(),
            snippet=BeautifulSoup(item.get("description", ""), "html.parser").get_text(" "),
            source="brave",
            uncertain=not _is_trusted(_host(item.get("url", "")), trusted_domains),
        )
        for item in items
        if item.get("url")
    ]


def _search_duckduckgo(query: str, trusted_domains: set[str]) -> list[SearchResult]:
    response = requests.get(
        "https://duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    for result in soup.select(".result"):
        link = result.select_one(".result__a")
        snippet = result.select_one(".result__snippet")
        if not link:
            continue
        url = _normalize_duckduckgo_url(link.get("href", ""))
        if not url.startswith("http"):
            continue
        host = _host(url)
        results.append(
            SearchResult(
                title=_clean_text(link.get_text(" ")),
                url=url,
                snippet=_clean_text(snippet.get_text(" ") if snippet else ""),
                source="duckduckgo",
                uncertain=not _is_trusted(host, trusted_domains),
            )
        )
    return results


def _normalize_duckduckgo_url(url: str) -> str:
    parsed = urlparse(unescape(url))
    if "duckduckgo.com" in parsed.netloc and parsed.query:
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            return uddg[0]
    return unescape(url)


def _dedupe_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for result in results:
        normalized = _canonical_url(result.url)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(result)
    return deduped


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _is_trusted(host: str, trusted_domains: set[str]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in trusted_domains)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def quote_query(query: str) -> str:
    return quote_plus(query)

