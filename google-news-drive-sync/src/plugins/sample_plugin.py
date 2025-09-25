"""Example plugin demonstrating the plugin interface."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from ..news_fetcher import NewsArticle


class SamplePlugin:
    """Return no results but documents the plugin contract."""

    name = "sample"

    async def fetch(
        self,
        config: Dict[str, Any],
        *,
        cache: Any | None = None,
        monitor: Any | None = None,
    ) -> Iterable[NewsArticle]:
        _ = (config, cache, monitor)
        return []


__all__ = ["SamplePlugin"]
