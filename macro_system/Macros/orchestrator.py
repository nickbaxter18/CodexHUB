"""Header & Purpose: agent orchestration utilities for macro execution."""

from __future__ import annotations

# === Imports / Dependencies ===
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from .engine import MacroEngine
from .planner import MacroPlanner
from .types import AgentAssignment, PlanStep

# === Types / Interfaces / Schemas ===
AgentMap = Mapping[str, str]


# === Core Logic / Implementation ===
DEFAULT_AGENT_MAP: Dict[str, str] = {
    "analytics": "Knowledge Agent",
    "architecture": "Architect Agent",
    "backend": "Backend Agent",
    "data": "Knowledge Agent",
    "database": "Backend Agent",
    "delivery": "CI/CD Agent",
    "deployment": "CI/CD Agent",
    "documentation": "Knowledge Agent",
    "frontend": "Frontend Agent",
    "observability": "CI/CD Agent",
    "orchestration": "Meta Agent",
    "performance": "Backend Agent",
    "quality": "QA Agent",
    "security": "CI/CD Agent",
    "strategy": "Architect Agent",
    "testing": "QA Agent",
    "ux": "QA Agent",
}


class MacroOrchestrator:
    """Coordinate macro plans across agent roles using metadata heuristics."""

    def __init__(
        self,
        engine: MacroEngine,
        *,
        agent_map: AgentMap | None = None,
        default_agent: str = "Meta Agent",
    ) -> None:
        self._engine = engine
        self._planner = MacroPlanner(engine)
        self._default_agent = default_agent
        merged_map: Dict[str, str] = {
            key.casefold(): value for key, value in DEFAULT_AGENT_MAP.items()
        }
        if agent_map:
            for domain, agent in agent_map.items():
                domain_key = domain.casefold()
                merged_map[domain_key] = agent
        self._agent_map = merged_map

    def agent_map(self) -> Dict[str, str]:
        """Return a copy of the active domain-to-agent mapping."""

        return dict(self._agent_map)

    def available_agents(self) -> Sequence[str]:
        """Return the set of agents referenced by the orchestrator."""

        agents: Dict[str, None] = {}
        for agent in self._agent_map.values():
            agents.setdefault(agent, None)
        agents.setdefault(self._default_agent, None)
        return list(agents.keys())

    def assign(
        self, macro_name: str, *, include_non_leaf: bool = False
    ) -> List[AgentAssignment]:
        """Return agent assignments for the specified macro."""

        plan = self._planner.build(macro_name)
        steps = plan.flatten() if include_non_leaf else plan.leaf_tasks()
        return self._build_assignments(steps)

    def assign_many(
        self, macro_names: Iterable[str], *, include_non_leaf: bool = False
    ) -> List[AgentAssignment]:
        """Return agent assignments spanning multiple macros."""

        collected: List[PlanStep] = []
        for name in macro_names:
            plan = self._planner.build(name)
            if include_non_leaf:
                collected.extend(plan.flatten())
            else:
                collected.extend(plan.leaf_tasks())
        return self._build_assignments(collected)

    def dispatch(
        self,
        macro_names: Iterable[str] | str,
        *,
        include_non_leaf: bool = False,
        format: str = "prompt",
    ) -> Dict[str, str]:
        """Return formatted instructions per agent for the given macros."""

        if isinstance(macro_names, str):
            names = [macro_names]
        else:
            names = list(macro_names)

        if not names:
            return {}

        assignments = self.assign_many(names, include_non_leaf=include_non_leaf)
        return self._format_assignments(assignments, format=format)

    def _build_assignments(self, steps: Sequence[PlanStep]) -> List[AgentAssignment]:
        buckets: MutableMapping[str, List[PlanStep]] = {}
        for step in steps:
            agent = self._resolve_agent(step.macro)
            buckets.setdefault(agent, []).append(step)
        return [AgentAssignment(agent=agent, steps=items) for agent, items in buckets.items()]

    def _format_assignments(
        self, assignments: Sequence[AgentAssignment], *, format: str
    ) -> Dict[str, str]:
        formatter = format.casefold()
        formatted: Dict[str, str] = {}
        for assignment in assignments:
            if formatter == "prompt":
                formatted[assignment.agent] = assignment.to_prompt()
            elif formatter == "outline":
                formatted[assignment.agent] = assignment.to_outline()
            elif formatter in {"text", "instructions"}:
                formatted[assignment.agent] = assignment.instructions_text()
            else:
                raise ValueError(
                    "Unknown assignment format. Expected 'prompt', 'outline', or 'text'."
                )
        return formatted

    def _resolve_agent(self, macro_name: str) -> str:
        macro = self._engine.describe(macro_name)
        metadata_agent = macro.metadata.get("agent")
        if isinstance(metadata_agent, str) and metadata_agent.strip():
            return metadata_agent.strip()
        domain = str(macro.metadata.get("domain", "")).casefold()
        if domain in self._agent_map:
            return self._agent_map[domain]
        return self._default_agent


# === Error & Edge Handling ===
# ``MacroPlanner.build`` propagates ``MacroNotFoundError`` and ``MacroCycleError``
# for invalid macro graphs; agent resolution defaults to ``default_agent`` when
# metadata is absent or unrecognised.


# === Performance Considerations ===
# Plans are built once per requested macro; assignments reuse lightweight
# :class:`PlanStep` instances to avoid duplicate expansion work.


# === Exports / Public API ===
__all__ = ["MacroOrchestrator", "DEFAULT_AGENT_MAP"]

