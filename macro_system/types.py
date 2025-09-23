"""Core types and exceptions for the macro system."""

# === Imports ===
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

# === Types ===


@dataclass(frozen=True)
class Macro:
    """Data container describing a macro definition."""

    name: str
    expansion: str
    calls: List[str]


class MacroError(Exception):
    """Base class for macro-related failures."""


class MacroNotFoundError(MacroError):
    """Raised when attempting to expand an undefined macro."""


class MacroCycleError(MacroError):
    """Raised when a cycle is detected during macro expansion."""


class MacroDefinitionError(MacroError):
    """Raised when macro definitions are invalid or malformed."""


@dataclass
class PlanStep:
    """Represents an actionable step produced from a macro expansion."""

    macro: str
    description: str
    children: List["PlanStep"] = field(default_factory=list)

    def to_outline(self) -> str:
        """Return a human-readable outline of this plan and its children."""

        lines: List[str] = []

        def _walk(step: "PlanStep", depth: int) -> None:
            indent = "  " * depth
            lines.append(f"{indent}- {step.macro}: {step.description}")
            for child in step.children:
                _walk(child, depth + 1)

        _walk(self, 0)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialise the plan hierarchy into a JSON-friendly dictionary."""

        return {
            "macro": self.macro,
            "description": self.description,
            "children": [child.to_dict() for child in self.children],
        }

    def leaf_tasks(self) -> List["PlanStep"]:
        """Return the leaves of the plan tree as actionable tasks."""

        tasks: List[PlanStep] = []

        def _gather(step: "PlanStep") -> None:
            if not step.children:
                tasks.append(step)
            else:
                for child in step.children:
                    _gather(child)

        _gather(self)
        return tasks


# === Exports ===
__all__ = [
    "Macro",
    "MacroError",
    "MacroNotFoundError",
    "MacroCycleError",
    "MacroDefinitionError",
    "PlanStep",
]
