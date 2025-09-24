"""Convenience exports for CodexHUB agent implementations."""

from .agent_base import Agent, AgentTaskError
from .knowledge_agent import (
    KnowledgeAgent as RetrievalKnowledgeAgent,
    KnowledgeRecord,
    KnowledgeSearchResult,
    KnowledgeStore,
)
from .meta_agent import MetaAgent
from .specialist_agents import (
    AgentTask,
    ArchitectAgent,
    BackendAgent,
    CICDAgent,
    FrontendAgent,
    KnowledgeAgent as SpecialistKnowledgeAgent,
    KnowledgeDocument,
    QAAgent,
    SpecialistAgent,
)

# Maintain backwards compatibility for callers expecting the specialist knowledge agent
KnowledgeAgent = SpecialistKnowledgeAgent

# Expose the retrieval-focused implementation with an explicit alias
KnowledgeRetrievalAgent = RetrievalKnowledgeAgent

__all__ = [
    "Agent",
    "AgentTask",
    "AgentTaskError",
    "ArchitectAgent",
    "BackendAgent",
    "CICDAgent",
    "FrontendAgent",
    "KnowledgeAgent",
    "KnowledgeDocument",
    "KnowledgeRecord",
    "KnowledgeRetrievalAgent",
    "KnowledgeSearchResult",
    "KnowledgeStore",
    "MetaAgent",
    "QAAgent",
    "SpecialistAgent",
]
