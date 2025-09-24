"""Collective agent combining lightweight crowd signals."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from ..config import get_config
from ..knowledge import retrieval
from ..utils.cache import SimpleCache
from .base import Agent


class CollectiveAgent(Agent):
    """Aggregate auxiliary intelligence from the knowledge graph."""

    def __init__(self) -> None:
        super().__init__(name="collective")
        self._config = get_config()
        self._cache = SimpleCache[str, Dict[str, Any]](maxsize=64, ttl=60.0)
        self._shared_events: List[Dict[str, Any]] = []

    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        query = context.get("query")
        if not query:
            request = context.get("request")
            query = getattr(request, "command", None) or getattr(request, "action", None)
        if not query:
            return context
        if not self._config.collective_opt_in:
            context.update({"signals": [], "top_tags": [], "opt_in": False})
            return context
        cached = self._cache.get(query)
        if cached:
            context.update(cached)
            return context
        results = retrieval.query(query, limit=5)
        tag_counter: Counter[str] = Counter()
        for item in results:
            tags = item.get("tags", [])
            if isinstance(tags, (list, tuple)):
                tag_counter.update(str(tag) for tag in tags)
        insights = {
            "signals": results,
            "top_tags": [tag for tag, _ in tag_counter.most_common(3)],
            "opt_in": True,
        }
        self._cache.set(query, insights)
        context.update(insights)
        signals = insights.get("signals", [])
        if isinstance(signals, list) and signals:
            self._shared_events.append(
                {
                    "query": query,
                    "top_tags": insights["top_tags"],
                    "count": len(signals),
                }
            )
            self._shared_events = self._shared_events[-50:]
        return context

    async def act(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Provide weighted recommendations from cached suggestions.
        query = str(payload.get("query", ""))
        insights = self._cache.get(query)
        if not insights:
            observed = await self.observe({"query": query})
            insights = self._cache.get(query) or observed
        weights: List[Dict[str, Any]] = []
        for item in insights.get("signals", []):
            weights.append({"id": str(item.get("id")), "weight": float(item.get("score", 0.0))})
        recent_shared = list(self._shared_events[-5:])
        return {
            "recommendations": weights,
            "shared_signals": recent_shared,
            "opt_in": self._config.collective_opt_in,
            **payload,
        }

    def metrics(self) -> Dict[str, Any]:
        """Return aggregate statistics for dashboards."""

        return {
            "shared_events": len(self._shared_events),
            "opt_in": self._config.collective_opt_in,
        }
