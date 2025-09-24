"""Base agent definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Agent(ABC):
    """Abstract base class for agents."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Observe context and optionally augment it."""

    @abstractmethod
    async def act(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Take an action based on provided payload."""
