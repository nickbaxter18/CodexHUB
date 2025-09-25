"""Coordinate fetching articles from multiple sources."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Sequence

from .cache import ArticleCache
from .news_fetcher import NewsArticle, fetch_news_async
from .monitor import MonitoringClient
from .rss_fetcher import fetch_rss_async
from .plugin_manager import discover_plugins, execute_plugins

logger = logging.getLogger(__name__)


async def _gather_results(
    tasks: Sequence[asyncio.Task],
    sources: Sequence[str],
    monitor: MonitoringClient | None,
) -> List[NewsArticle]:
    articles: List[NewsArticle] = []
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    for source_name, result in zip(sources, gathered, strict=False):
        if isinstance(result, Exception):
            logger.exception("Source %s failed", source_name, exc_info=result)
            if monitor is not None:
                monitor.record_error(source_name, result)
            continue
        articles.extend(result)
        if monitor is not None:
            monitor.record_articles(source_name, len(result))
    return articles


def _deduplicate(articles: Iterable[NewsArticle]) -> List[NewsArticle]:
    seen: Dict[str, NewsArticle] = {}
    for article in articles:
        key = article.url or article.title
        if not key:
            continue
        if key not in seen:
            seen[key] = article
    return list(seen.values())


async def fetch_all_articles(
    config: Dict[str, Any],
    *,
    cache: ArticleCache | None = None,
    monitor: MonitoringClient | None = None,
    news_fetcher: Callable[..., Awaitable[List[NewsArticle]]] | None = None,
    rss_fetcher: Callable[..., Awaitable[List[NewsArticle]]] | None = None,
    base_dir: Path | None = None,
) -> List[NewsArticle]:
    """Fetch articles from all configured sources concurrently."""

    news_fetcher = news_fetcher or fetch_news_async
    rss_fetcher = rss_fetcher or fetch_rss_async

    tasks: List[asyncio.Task] = []
    labels: List[str] = []

    news_cfg = config.get("news_api", {})
    api_key = news_cfg.get("api_key")
    if api_key:
        base_query = {
            "language": news_cfg.get("language", "en"),
            "country": news_cfg.get("country"),
            "pageSize": news_cfg.get(
                "page_size",
                news_cfg.get("pageSize", 20),
            ),
        }
        max_articles = news_cfg.get("max_articles")
        topics: Sequence[str] = news_cfg.get("topics") or []
        base_url = news_cfg.get(
            "base_url",
            "https://newsapi.org/v2/top-headlines",
        )
        tasks.append(
            asyncio.create_task(
                news_fetcher(
                    api_key,
                    base_query,
                    base_url=base_url,
                    max_articles=max_articles,
                    topics=topics,
                )
            )
        )
        labels.append("news_api")
    else:
        logger.warning("news_api.api_key missing; skipping NewsAPI source")

    sources_cfg = config.get("sources", {})
    rss_feeds: Sequence[str] = []
    rss_limit = None
    if sources_cfg:
        rss_feeds = sources_cfg.get("rss", [])
        rss_limit = sources_cfg.get("rss_limit_per_feed")
    if rss_feeds:
        tasks.append(asyncio.create_task(rss_fetcher(rss_feeds, limit_per_feed=rss_limit)))
        labels.append("rss")

    plugin_articles: List[NewsArticle] = []
    plugin_cfg = config.get("plugins", {})
    plugin_enabled = plugin_cfg.get("enabled", True)

    if not tasks and not (plugin_enabled and plugin_cfg):
        logger.warning("No news sources configured; returning empty result set")
        return []

    articles: List[NewsArticle] = []
    if tasks:
        articles.extend(await _gather_results(tasks, labels, monitor))

    if plugin_enabled and plugin_cfg:
        package_names: Sequence[str] = plugin_cfg.get("packages", [])
        file_paths: Sequence[str] = plugin_cfg.get("paths", [])
        base_path = base_dir or Path.cwd()
        resolved_paths: List[Path] = []
        for item in file_paths:
            candidate = Path(item)
            if not candidate.is_absolute():
                candidate = base_path / candidate
            resolved_paths.append(candidate)
        plugins = discover_plugins(
            packages=package_names,
            paths=resolved_paths,
        )
        if plugins:
            plugin_settings = plugin_cfg.get("settings", {})
            plugin_articles = await execute_plugins(
                plugins,
                plugin_settings,
                cache=cache,
                monitor=monitor,
            )
            articles.extend(plugin_articles)

    deduped = _deduplicate(articles)

    if cache is not None:
        fresh = cache.filter_new(deduped)
        cache.record(fresh)
        return fresh

    return deduped


__all__ = ["fetch_all_articles"]
