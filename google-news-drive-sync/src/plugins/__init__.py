"""Plugin interfaces for extending news acquisition."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Protocol, runtime_checkable

from ..news_fetcher import NewsArticle


class PluginError(RuntimeError):
    """Raised when plugin loading or execution fails."""


@runtime_checkable
class NewsPlugin(Protocol):
    """Protocol describing the expected interface for plugins."""

    name: str

    async def fetch(
        self,
        config: Dict[str, Any],
        *,
        cache: Any | None = None,
        monitor: Any | None = None,
    ) -> Iterable[NewsArticle]:
        """Return a collection of :class:`NewsArticle` items."""


__all__ = ["NewsPlugin", "PluginError", "NewsArticle"]
