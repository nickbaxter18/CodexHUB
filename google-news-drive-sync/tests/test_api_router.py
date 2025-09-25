import asyncio

from src.api_router import fetch_all_articles
from src.cache import ArticleCache
from src.news_fetcher import NewsArticle
from src.monitor import MonitoringClient


def test_fetch_all_articles_deduplicates(tmp_path):
    article = NewsArticle(
        title="Example",
        description=None,
        url="https://example.com",
        published_at=None,
        source="API",
    )

    async def fake_news_fetcher(*args, **kwargs):
        return [article]

    async def fake_rss_fetcher(*args, **kwargs):
        return [article]

    cache = ArticleCache(tmp_path / "cache.db", retention_days=1)
    config = {
        "news_api": {"api_key": "key"},
        "sources": {"rss": ["feed"]},
    }

    results = asyncio.run(
        fetch_all_articles(
            config,
            cache=cache,
            news_fetcher=fake_news_fetcher,
            rss_fetcher=fake_rss_fetcher,
        )
    )

    assert len(results) == 1
    assert cache.filter_new([article]) == []


def test_fetch_all_articles_handles_missing_sources():
    config = {"news_api": {}, "sources": {}}
    results = asyncio.run(fetch_all_articles(config))
    assert results == []


def test_fetch_all_articles_updates_monitor():
    article = NewsArticle(
        title="Example",
        description=None,
        url="https://example.com",
        published_at=None,
        source="API",
    )

    async def fake_news_fetcher(*args, **kwargs):
        return [article]

    monitor = MonitoringClient()
    config = {"news_api": {"api_key": "key"}}

    asyncio.run(fetch_all_articles(config, monitor=monitor, news_fetcher=fake_news_fetcher))

    snapshot = monitor.snapshot()
    assert snapshot.articles_processed == 1
    assert snapshot.source_counts["news_api"] == 1


def test_fetch_all_articles_with_plugins(tmp_path):
    plugin_path = tmp_path / "plugin.py"
    plugin_path.write_text(
        """
from typing import Any, Dict

from src.news_fetcher import NewsArticle


class DemoPlugin:
    name = "demo"

    async def fetch(self, config: Dict[str, Any], *, cache=None, monitor=None):
        return [
            NewsArticle(
                title="Plugin",
                description=None,
                url="https://example.com/plugin",
                published_at=None,
                source="demo",
            )
        ]
"""
    )

    config = {
        "news_api": {},
        "sources": {},
        "plugins": {
            "enabled": True,
            "paths": [str(plugin_path)],
        },
    }

    results = asyncio.run(fetch_all_articles(config, base_dir=tmp_path))
    assert len(results) == 1
    assert results[0].title == "Plugin"
