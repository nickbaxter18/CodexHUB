"""News API client for Google News Drive Sync."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)


try:  # pragma: no cover - optional dependency used in production
    import aiohttp
except Exception:  # pragma: no cover - aiohttp may be unavailable during tests
    aiohttp = None  # type: ignore[assignment]


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


async def _request_page(
    session: Any,
    *,
    base_url: str,
    params: Dict[str, Any],
    api_key: str,
    timeout: int,
) -> Dict[str, Any]:
    """Perform an HTTP GET request for a page of articles."""

    headers = {"X-Api-Key": api_key}
    async with session.get(
        base_url,
        params=params,
        headers=headers,
        timeout=timeout,
    ) as response:
        status = getattr(response, "status", None)
        if status == 429:
            raise NewsFetcherError("Rate limit exceeded while fetching news.")
        if status is not None and status >= 400:
            text = await response.text()
            message = f"News API request failed with status {status}: {text}"
            raise NewsFetcherError(message)
        return await response.json()


def _parse_articles(payload: Dict[str, Any]) -> List[NewsArticle]:
    raw_articles: Iterable[Dict[str, Any]] = payload.get("articles") or []
    parsed: List[NewsArticle] = []
    for item in raw_articles:
        if not isinstance(item, dict):
            continue
        article = NewsArticle.from_payload(item)
        if not article.title or not article.url:
            continue
        parsed.append(article)
    return parsed


async def _collect_topic(
    session: Any,
    api_key: str,
    base_url: str,
    params: Dict[str, Any],
    *,
    topic: str | None,
    limit: Optional[int],
    timeout: int,
    max_pages: int,
) -> List[NewsArticle]:
    topic_params = dict(params)
    if topic:
        topic_params["q"] = topic

    articles: List[NewsArticle] = []
    total_results: Optional[int] = None
    current_page = 1

    while True:
        topic_params["page"] = current_page
        payload = await _request_page(
            session,
            base_url=base_url,
            params=topic_params,
            api_key=api_key,
            timeout=timeout,
        )

        if total_results is None:
            total_results = payload.get("totalResults")

        batch = _parse_articles(payload)
        articles.extend(batch)

        if limit and len(articles) >= limit:
            return articles[:limit]
        if not batch:
            break
        if total_results is not None and len(articles) >= total_results:
            break

        current_page += 1
        if current_page > max_pages:
            break

    return articles


async def fetch_news_async(
    api_key: str,
    query: Dict[str, Any],
    *,
    base_url: str = "https://newsapi.org/v2/top-headlines",
    max_articles: Optional[int] = None,
    topics: Optional[Sequence[str]] = None,
    session: Any | None = None,
    timeout: int = 10,
    max_pages: int = 5,
) -> List[NewsArticle]:
    """Fetch news articles concurrently for each configured topic."""

    if not api_key:
        raise ValueError("API key is required to fetch news.")

    params = dict(query)
    page_size = int(params.get("pageSize", params.get("page_size", 20)))
    params.setdefault("pageSize", page_size)
    params.pop("q", None)  # topic-specific queries are handled per task

    topics = topics or []
    limit = max_articles or int(params.get("max_articles", 0)) or None

    if session is None:
        if aiohttp is None:
            raise NewsFetcherError(
                ("aiohttp is required for asynchronous fetching " "but is not installed.")
            )

        # pragma: no cover - requires aiohttp
        async with aiohttp.ClientSession() as auto_session:
            return await fetch_news_async(
                api_key,
                params,
                base_url=base_url,
                max_articles=limit,
                topics=topics,
                session=auto_session,
                timeout=timeout,
                max_pages=max_pages,
            )

    tasks = []
    task_topics: Sequence[str | None] = topics or [None]
    per_topic_limit: Optional[int] = None
    if limit and task_topics:
        per_topic_limit = max(1, limit // len(task_topics))

    for topic in task_topics:
        tasks.append(
            asyncio.create_task(
                _collect_topic(
                    session,
                    api_key,
                    base_url,
                    params,
                    topic=topic,
                    limit=per_topic_limit,
                    timeout=timeout,
                    max_pages=max_pages,
                )
            )
        )

    articles: List[NewsArticle] = []
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.exception("Topic fetch failed", exc_info=result)
            continue
        articles.extend(result)

    articles.sort(
        key=lambda item: item.published_at or datetime.min,
        reverse=True,
    )
    if limit:
        articles = articles[:limit]

    logger.info(
        "Fetched %s articles across %s topics",
        len(articles),
        len(task_topics),
    )
    return articles


def fetch_news(
    api_key: str,
    query: Dict[str, Any],
    *,
    base_url: str = "https://newsapi.org/v2/top-headlines",
    max_articles: Optional[int] = None,
    topics: Optional[Sequence[str]] = None,
    session: Any | None = None,
    timeout: int = 10,
    max_pages: int = 5,
) -> List[NewsArticle]:
    """Synchronous wrapper around :func:`fetch_news_async`."""

    coroutine = fetch_news_async(
        api_key,
        query,
        base_url=base_url,
        max_articles=max_articles,
        topics=topics,
        session=session,
        timeout=timeout,
        max_pages=max_pages,
    )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    raise RuntimeError(
        ("fetch_news cannot be invoked from an active event loop; " "use fetch_news_async instead.")
    )
