"""Header & Purpose: planning utilities for macro execution roadmaps."""

from __future__ import annotations

# === Imports / Dependencies ===
import json
from typing import Iterable, List

from .engine import MacroEngine
from .types import MacroCycleError, PlanStep

# === Types / Interfaces / Schemas ===
# Plans reuse :class:`PlanStep` dataclasses for hierarchical structures.


# === Core Logic / Implementation ===
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

    def render_markdown(self, macro_name: str) -> str:
        """Render a Markdown document describing the macro execution plan."""

        plan = self.build(macro_name)
        return plan.to_markdown()

    def render_json(self, macro_name: str, *, indent: int = 2) -> str:
        """Return a JSON string representing the macro plan tree."""

        plan = self.build(macro_name)
        return json.dumps(plan.to_dict(), indent=indent)

    def tasks(self, macro_name: str) -> List[str]:
        """Return leaf tasks for ``macro_name`` as human-readable strings."""

        plan = self.build(macro_name)
        return [f"{step.macro}: {step.description}" for step in plan.leaf_tasks()]

    def _build_recursive(self, name: str, stack: List[str]) -> PlanStep:
        if name in stack:
            cycle = stack[stack.index(name) :] + [name]
            raise MacroCycleError(" -> ".join(cycle))

        macro = self._engine.describe(name)
        stack.append(name)
        children = [self._build_recursive(child, stack) for child in macro.calls]
        stack.pop()

        return PlanStep(macro=name, description=macro.expansion, children=children)


# === Error & Edge Handling ===
# Cycles detected during planning raise ``MacroCycleError`` for clarity.


# === Performance Considerations ===
# Plan construction reuses engine caching implicitly through ``describe`` lookups.


# === Exports / Public API ===
__all__ = ["MacroPlanner"]
