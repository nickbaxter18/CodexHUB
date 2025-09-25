"""News API client for Google News Drive Sync."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import requests
from requests import Response

logger = logging.getLogger(__name__)


class NewsFetcherError(RuntimeError):
    """Raised when fetching news fails irrecoverably."""


@dataclass(frozen=True)
class NewsArticle:
    """Representation of a news article returned by the API."""

    title: str
    description: str | None
    url: str
    published_at: datetime | None
    source: str | None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "NewsArticle":
        published_at = payload.get("publishedAt")
        parsed_date: datetime | None = None
        if isinstance(published_at, str):
            try:
                iso_value = published_at.replace("Z", "+00:00")
                parsed_date = datetime.fromisoformat(iso_value)
            except ValueError:
                parsed_date = None

        source_info = payload.get("source")
        source_name: str | None = None
        if isinstance(source_info, dict):
            source_name = source_info.get("name")

        return cls(
            title=payload.get("title") or "",
            description=payload.get("description"),
            url=payload.get("url") or "",
            published_at=parsed_date,
            source=source_name,
        )


def _handle_error(response: Response) -> None:
    if response.status_code == 429:
        raise NewsFetcherError("Rate limit exceeded while fetching news.")
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover
        raise NewsFetcherError("News API request failed") from exc


def fetch_news(
    api_key: str,
    query: Dict[str, Any],
    *,
    session: Optional[requests.Session] = None,
    base_url: str = "https://newsapi.org/v2/top-headlines",
    max_articles: Optional[int] = None,
) -> List[NewsArticle]:
    """Fetch news articles from the configured API.

    Args:
        api_key: API key for the news provider.
        query: Dictionary of query parameters (e.g., topics, language).
        session: Optional requests session for connection reuse.
        base_url: API endpoint to query.
        max_articles: Optional hard limit on articles to fetch.
    """

    if not api_key:
        raise ValueError("API key is required to fetch news.")

    params = dict(query)
    page_size = int(params.get("pageSize", params.get("page_size", 20)))
    params.setdefault("pageSize", page_size)

    limit = max_articles or int(params.get("max_articles", 0)) or None
    articles: List[NewsArticle] = []
    current_page = 1
    session_to_use = session or requests.Session()
    total_results: Optional[int] = None

    while True:
        params["page"] = current_page
        logger.debug("Requesting news page %s", current_page)

        response = session_to_use.get(
            base_url,
            params=params,
            timeout=10,
            headers={"X-Api-Key": api_key},
        )
        _handle_error(response)
        payload = response.json()

        if total_results is None:
            total_results = payload.get("totalResults")

        raw_articles: Iterable[Dict[str, Any]] = payload.get("articles") or []
        batch: List[NewsArticle] = []
        for item in raw_articles:
            if not isinstance(item, dict):
                continue
            article = NewsArticle.from_payload(item)
            if not article.title or not article.url:
                continue
            batch.append(article)

        articles.extend(batch)

        if limit and len(articles) >= limit:
            articles = articles[:limit]
            break

        if not batch:
            break

        if total_results is not None and len(articles) >= total_results:
            break

        current_page += 1
        if current_page > 5:  # Safety cap for Stage 1
            break

    logger.info("Fetched %s articles", len(articles))
    return articles
