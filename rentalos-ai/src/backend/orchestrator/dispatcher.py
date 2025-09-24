"""Dispatcher utilities for orchestrator."""

from __future__ import annotations

from typing import Any, Dict

from . import registry


async def dispatch(agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    agent = registry.get(agent_name)
    result = await agent.run(payload)
    return {
        "agent": result.name,
        "generated_at": result.generated_at.isoformat(),
        "data": result.data,
    }
