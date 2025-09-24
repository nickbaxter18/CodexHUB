"""Knowledge agent backed by the Stage 2 knowledge graph."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..errors import KnowledgeError
from ..knowledge import retrieval
from ..knowledge.graph import KnowledgeRecord
from ..types import KnowledgeQueryRequest
from .base import Agent


class KnowledgeAgent(Agent):
    """Expose knowledge graph lookups and enrichment."""

    def __init__(self) -> None:
        super().__init__(name="knowledge")
        self._ingested = 0

    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        query_text: Optional[str] = None
        request = context.get("request")
        if request is not None:
            query_text = getattr(request, "command", None) or getattr(request, "action", None)
        if not query_text:
            query_text = context.get("query")
        results: Dict[str, Any] = {}
        if query_text:
            results["suggestions"] = retrieval.query(query_text, limit=3)
        context.update(results)
        return context

    async def act(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "record" in payload:
            record = payload["record"]
            if isinstance(record, KnowledgeRecord):
                retrieval.ingest(record)
                self._ingested += 1
                return {"ingested": record.identifier}
        request = KnowledgeQueryRequest(
            query=str(payload.get("query", "")),
            limit=int(payload.get("limit", 5)),
        )
        results = retrieval.query(request.query, limit=request.limit)
        neighbours = None
        if payload.get("include_neighbours") and results:
            first_id = str(results[0]["id"])
            neighbours = retrieval.neighbours(first_id, depth=int(payload.get("depth", 1)))
        response: Dict[str, Any] = {"results": results}
        if neighbours is not None:
            response["neighbours"] = neighbours
        return response

    def stats(self) -> Dict[str, int]:
        """Return metrics for UI consumption."""

        try:
            graph_stats = retrieval.stats()
        except KnowledgeError:
            graph_stats = {"nodes": 0, "edges": 0}
        return {"ingested": self._ingested, **graph_stats}
