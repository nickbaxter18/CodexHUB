"""Knowledge retrieval helpers built on the knowledge graph."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List

from ..config import get_config
from ..errors import KnowledgeError
from .graph import KnowledgeGraph, KnowledgeRecord


@lru_cache()
def _load_graph() -> KnowledgeGraph:
    config = get_config()
    if not config.knowledge_sources:
        raise KnowledgeError("No knowledge sources configured")
    return KnowledgeGraph.from_sources(tuple(config.knowledge_sources))


def query(text: str, limit: int = 5) -> List[Dict[str, object]]:
    """Query the knowledge graph for relevant documents."""

    graph = _load_graph()
    return graph.query(text=text, limit=limit)


def neighbours(identifier: str, depth: int = 1) -> List[str]:
    graph = _load_graph()
    return graph.neighbours(identifier, depth=depth)


def ingest(record: KnowledgeRecord) -> None:
    graph = _load_graph()
    graph.add_or_update(record)


def clear_cache() -> None:
    _load_graph.cache_clear()


def stats() -> Dict[str, int]:
    """Expose summary information about the loaded knowledge graph."""

    graph = _load_graph()
    return graph.stats()
