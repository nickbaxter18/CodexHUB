"""Asynchronous RSS feed fetcher for auxiliary news sources."""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Iterable, List, Sequence

from .news_fetcher import NewsArticle, NewsFetcherError

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional runtime dependency
    import aiohttp
except Exception:  # pragma: no cover - dependency may be missing during tests
    aiohttp = None  # type: ignore[assignment]


class RssFetcherError(RuntimeError):
    """Raised when fetching RSS feeds fails irrecoverably."""


async def _fetch_feed(session: Any, url: str, timeout: int) -> str:
    """Retrieve the raw RSS payload for *url*."""

    async with session.get(url, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status >= 400:
            text = await response.text()
            message = "RSS request failed for " f"{url} with status {status}: {text}"
            raise RssFetcherError(message)
        return await response.text()


def _parse_feed(
    payload: str,
    *,
    fallback_source: str | None = None,
) -> List[NewsArticle]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:  # pragma: no cover
        raise RssFetcherError("Failed to parse RSS feed") from exc

    channel_title = None
    channel = root.find("channel")
    if channel is not None:
        title_node = channel.find("title")
        if title_node is not None and title_node.text:
            channel_title = title_node.text.strip()

    articles: List[NewsArticle] = []
    items: Iterable[ET.Element] = root.findall(".//item")
    for item in items:
        title_node = item.find("title")
        link_node = item.find("link")
        description_node = item.find("description")
        pub_date_node = item.find("pubDate")

        title = ""
        if title_node is not None:
            title = (title_node.text or "").strip()
        link = ""
        if link_node is not None:
            link = (link_node.text or "").strip()
        description = (
            description_node.text.strip()
            if description_node is not None and description_node.text
            else None
        )
        published_at: datetime | None = None
        if pub_date_node is not None and pub_date_node.text:
            try:
                published_at = parsedate_to_datetime(pub_date_node.text)
            except (TypeError, ValueError):
                published_at = None

        if not title or not link:
            continue

        source = channel_title or fallback_source
        articles.append(
            NewsArticle(
                title=title,
                description=description,
                url=link,
                published_at=published_at,
                source=source,
            )
        )

    return articles


async def fetch_rss_async(
    feeds: Sequence[str],
    *,
    session: Any | None = None,
    timeout: int = 10,
    limit_per_feed: int | None = None,
) -> List[NewsArticle]:
    """Fetch articles from the provided RSS *feeds* concurrently."""

    if not feeds:
        return []

    async def _collect(session_obj: Any, feed_url: str) -> List[NewsArticle]:
        payload = await _fetch_feed(session_obj, feed_url, timeout)
        articles = _parse_feed(payload, fallback_source=feed_url)
        if limit_per_feed is None:
            return articles
        return articles[:limit_per_feed]

    if session is None:
        if aiohttp is None:
            raise NewsFetcherError("aiohttp is required for RSS fetching but is not installed.")

        # pragma: no cover - requires aiohttp
        async with aiohttp.ClientSession() as auto_session:
            return await fetch_rss_async(
                feeds,
                session=auto_session,
                timeout=timeout,
                limit_per_feed=limit_per_feed,
            )

    tasks = [asyncio.create_task(_collect(session, feed)) for feed in feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles: List[NewsArticle] = []
    for feed_url, result in zip(feeds, results, strict=False):
        if isinstance(result, Exception):
            logger.exception(
                "RSS fetch failed for %s",
                feed_url,
                exc_info=result,
            )
            continue
        articles.extend(result)

    logger.info(
        "Fetched %s RSS articles from %s feeds",
        len(articles),
        len(feeds),
    )
    return articles


__all__ = ["RssFetcherError", "fetch_rss_async"]
