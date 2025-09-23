"""Core domain types, schemas, and error classes for the macro system."""

from __future__ import annotations
"""Header & Purpose: strongly-typed domain models for macro catalogues."""

# === Imports / Dependencies ===
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence

# === Types / Interfaces / Schemas ===


@dataclass(frozen=True)
class Macro:
    """Immutable representation of a macro definition loaded from JSON."""

    name: str
    expansion: str
    calls: List[str]
    metadata: Mapping[str, object] = field(default_factory=dict)

    # === Core Logic / Implementation ===
    def describe(self) -> Dict[str, object]:
        """Return a serialisable dictionary for inspection and auditing."""

        return {
            "name": self.name,
            "expansion": self.expansion,
            "calls": list(self.calls),
            "metadata": dict(self.metadata),
        }


class MacroError(Exception):
    """Base class for macro-related failures."""


class MacroNotFoundError(MacroError):
    """Raised when attempting to expand or inspect an undefined macro."""


class MacroCycleError(MacroError):
    """Raised when a cycle is detected during macro expansion or planning."""


class MacroDefinitionError(MacroError):
    """Raised when macro definitions are invalid, malformed, or inconsistent."""


class MacroRenderError(MacroError):
    """Raised when applying context to macro expansions fails."""


class MacroValidationError(MacroError):
    """Raised when catalogue-wide validation fails during audits."""


@dataclass(frozen=True)
class MacroStats:
    """Aggregate statistics describing the structure of a macro catalogue."""

    total_macros: int
    root_macros: Sequence[str]
    leaf_macros: Sequence[str]
    max_depth: int
    average_branching_factor: float

    # === Core Logic / Implementation ===
    def to_dict(self) -> Dict[str, object]:
        """Represent the statistics as a dictionary for JSON emission."""

        return {
            "total_macros": self.total_macros,
            "root_macros": list(self.root_macros),
            "leaf_macros": list(self.leaf_macros),
            "max_depth": self.max_depth,
            "average_branching_factor": self.average_branching_factor,
        }


@dataclass(frozen=True)
class MacroAudit:
    """Structured summary describing catalogue health and anomalies."""

    undefined_references: Mapping[str, Sequence[str]]
    cycles: Sequence[Sequence[str]]
    unreachable_macros: Sequence[str]
    entrypoints: Sequence[str]
    stats: MacroStats

    # === Core Logic / Implementation ===
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the audit result."""

        return {
            "undefined_references": {
                macro: list(missing) for macro, missing in self.undefined_references.items()
            },
            "cycles": [list(cycle) for cycle in self.cycles],
            "unreachable_macros": list(self.unreachable_macros),
            "entrypoints": list(self.entrypoints),
            "stats": self.stats.to_dict(),
        }


@dataclass
class PlanStep:
    """Represents an actionable plan node derived from macro expansion."""

    macro: str
    description: str
    children: List["PlanStep"] = field(default_factory=list)

    # === Core Logic / Implementation ===
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

    def to_dict(self) -> Dict[str, object]:
        """Serialise the plan hierarchy into a JSON-friendly dictionary."""

        return {
            "macro": self.macro,
            "description": self.description,
            "children": [child.to_dict() for child in self.children],
        }

    def to_markdown(self, heading_level: int = 2) -> str:
        """Render the plan tree as a Markdown document."""

        lines: List[str] = []

        def _walk(step: "PlanStep", depth: int) -> None:
            heading = "#" * max(1, heading_level + depth)
            lines.append(f"{heading} {step.macro}\n\n{step.description}\n")
            for child in step.children:
                _walk(child, depth + 1)

        _walk(self, 0)
        return "\n".join(lines).strip()

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

    def flatten(self) -> List["PlanStep"]:
        """Return the plan nodes in preorder traversal."""

        ordered: List[PlanStep] = []

        def _walk(step: "PlanStep") -> None:
            ordered.append(step)
            for child in step.children:
                _walk(child)

        _walk(self)
        return ordered


@dataclass
class AgentAssignment:
    """Group of plan steps allocated to a specific agent role."""

    agent: str
    steps: List[PlanStep] = field(default_factory=list)

    # === Core Logic / Implementation ===
    def macros(self) -> List[str]:
        """Return the macro identifiers associated with this assignment."""

        return [step.macro for step in self.steps]

    def instructions(self) -> List[str]:
        """Return the textual instructions for each assigned plan step."""

        return [step.description for step in self.steps]

    def instructions_text(self) -> str:
        """Return concatenated instructions suitable for prompting agents."""

        return "\n\n".join(self.instructions())

    def to_prompt(self, include_header: bool = True) -> str:
        """Render a conversational prompt tailored for the assigned agent."""

        lines: List[str] = []
        if include_header:
            lines.append(
                f"You are {self.agent}. Execute the following tasks with precision:"
            )
        for step in self.steps:
            lines.append(f"- {step.macro}: {step.description}")
        return "\n".join(lines)

    def to_outline(self) -> str:
        """Render a Markdown outline listing this agent's responsibilities."""

        lines: List[str] = [f"## {self.agent}"]
        for step in self.steps:
            lines.append(f"- {step.macro}: {step.description}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, object]:
        """Serialise the assignment into a JSON-friendly dictionary."""

        return {
            "agent": self.agent,
            "macros": self.macros(),
            "steps": [
                {"macro": step.macro, "description": step.description}
                for step in self.steps
            ],
            "instructions": self.instructions(),
            "instructions_text": self.instructions_text(),
            "prompt": self.to_prompt(),
        }


# === Error & Edge Handling ===
# Error classes defined above provide specific failure modes for catalogue issues.


# === Performance Considerations ===
# Dataclasses are lightweight and immutable where appropriate to support caching.


# === Exports / Public API ===
__all__ = [
    "Macro",
    "MacroAudit",
    "MacroCycleError",
    "MacroDefinitionError",
    "MacroError",
    "MacroNotFoundError",
    "MacroRenderError",
    "MacroStats",
    "MacroValidationError",
    "PlanStep",
    "AgentAssignment",
]
