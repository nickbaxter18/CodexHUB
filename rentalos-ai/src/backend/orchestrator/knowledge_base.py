"""Placeholder knowledge base integration for Stage 2."""

from __future__ import annotations

from typing import Dict, List


class KnowledgeBaseClient:
    """Lightweight in-memory knowledge base used for Stage 1 tests."""

    def __init__(self) -> None:
        self._relationships: Dict[str, List[str]] = {}

    def add_relationship(self, key: str, value: str) -> None:
        self._relationships.setdefault(key, []).append(value)

    def related(self, key: str) -> List[str]:
        return list(self._relationships.get(key, []))


knowledge_base = KnowledgeBaseClient()
