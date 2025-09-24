"""Utilities for bootstrapping knowledge agents with repository NDJSON corpora."""

from .corpus_loader import (
    KnowledgeCorpusLoader,
    bootstrap_repository_knowledge,
    discover_default_knowledge_paths,
)

__all__ = [
    "KnowledgeCorpusLoader",
    "bootstrap_repository_knowledge",
    "discover_default_knowledge_paths",
]
