"""Planner utilities that turn macro definitions into actionable plans."""

# === Imports ===
from __future__ import annotations

from typing import Iterable, List

from .engine import MacroEngine
from .types import MacroCycleError, PlanStep

# === Implementation ===


class MacroPlanner:
    """Construct hierarchical plans from macros for practical execution."""

    def __init__(self, engine: MacroEngine):
        self._engine = engine

    def build(self, macro_name: str) -> PlanStep:
        """Build a :class:`PlanStep` tree for ``macro_name``."""

        return self._build_recursive(macro_name, [])

    def build_many(self, macro_names: Iterable[str]) -> List[PlanStep]:
        """Build plan trees for several macros."""

        return [self.build(name) for name in macro_names]

    def render_outline(self, macro_name: str) -> str:
        """Return a formatted outline for ``macro_name`` suitable for prompts."""

        plan = self.build(macro_name)
        return plan.to_outline()

    def _build_recursive(self, name: str, stack: List[str]) -> PlanStep:
        if name in stack:
            cycle = stack[stack.index(name) :] + [name]
            raise MacroCycleError(" -> ".join(cycle))

        macro = self._engine.describe(name)
        stack.append(name)
        children = [self._build_recursive(child, stack) for child in macro.calls]
        stack.pop()

        return PlanStep(
            macro=name,
            description=macro.expansion,
            owner_agent=macro.owner_agent,
            outcomes=macro.outcomes,
            acceptance_criteria=macro.acceptance_criteria,
            qa_hooks=macro.qa_hooks,
            phase=macro.phase,
            priority=macro.priority,
            status=macro.status,
            estimated_duration=macro.estimated_duration,
            tags=macro.tags,
            version=macro.version,
            children=children,
        )


# === Exports ===
__all__ = ["MacroPlanner"]
