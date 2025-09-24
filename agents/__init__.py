"""
SECTION: Header & Purpose
    - Aggregates agent-facing utilities for consumers of the QA framework.

SECTION: Imports / Dependencies
    - Provides convenient imports for the base agent class, meta agent implementation, and the
      domain-specific specialist agents introduced in the governance roadmap.

SECTION: Exports / Public API
    - ``Agent`` and ``MetaAgent`` classes together with concrete specialist agents for
      architecture, frontend, backend, QA, CI/CD, and knowledge management.
"""

from .agent_base import Agent, AgentTaskError
from .knowledge_agent import KnowledgeAgent, KnowledgeRecord, KnowledgeSearchResult, KnowledgeStore
from .meta_agent import MetaAgent
from .specialist_agents import (
    AgentTask,
    ArchitectAgent,
    BackendAgent,
    CICDAgent,
    FrontendAgent,
    KnowledgeAgent,
    KnowledgeDocument,
    QAAgent,
    SpecialistAgent,
)

__all__ = [
    "Agent",
<<<<<<< HEAD
    "AgentTask",
    "AgentTaskError",
    "ArchitectAgent",
    "BackendAgent",
    "CICDAgent",
    "FrontendAgent",
    "KnowledgeAgent",
    "KnowledgeDocument",
    "MetaAgent",
    "QAAgent",
    "SpecialistAgent",
=======
    "AgentTaskError",
    "KnowledgeAgent",
    "KnowledgeRecord",
    "KnowledgeSearchResult",
    "KnowledgeStore",
    "MetaAgent",
>>>>>>> origin/codex/establish-repository-audit-process
]
