"""
SECTION: Header & Purpose
    - Aggregates agent-facing utilities for consumers of the QA framework.

SECTION: Imports / Dependencies
    - Provides convenient imports for the base agent class and meta agent implementation.

SECTION: Exports / Public API
    - ``Agent`` and ``MetaAgent`` classes.
"""

from .agent_base import Agent, AgentTaskError
from .meta_agent import MetaAgent

__all__ = ["Agent", "AgentTaskError", "MetaAgent"]
