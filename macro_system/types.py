"""Core types and exceptions for the macro system."""

# === Imports ===
from __future__ import annotations

# === Imports ===
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional

# === Types ===


@dataclass(frozen=True)
class Macro:
    """Data container describing a macro definition."""

    name: str
    expansion: str
    calls: List[str]
    owner_agent: Optional[str] = None
    outcomes: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    qa_hooks: List[str] = field(default_factory=list)
    phase: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    estimated_duration: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    version: Optional[str] = None


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
    owner_agent: Optional[str] = None
    outcomes: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    qa_hooks: List[str] = field(default_factory=list)
    phase: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    estimated_duration: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    version: Optional[str] = None
    children: List["PlanStep"] = field(default_factory=list)

    def to_outline(self) -> str:
        """Return a human-readable outline of this plan and its children."""

        lines: List[str] = []

        def _walk(step: "PlanStep", depth: int) -> None:
            indent = "  " * depth
            agent = f" [{step.owner_agent}]" if step.owner_agent else ""
            status = f" ({step.status})" if step.status else ""
            priority = f" <{step.priority}>" if step.priority else ""
            lines.append(
                f"{indent}- {step.macro}{agent}{priority}{status}: {step.description}"
            )
            for child in step.children:
                _walk(child, depth + 1)

        _walk(self, 0)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialise the plan hierarchy into a JSON-friendly dictionary."""

        return {
            "macro": self.macro,
            "description": self.description,
            "ownerAgent": self.owner_agent,
            "outcomes": list(self.outcomes),
            "acceptanceCriteria": list(self.acceptance_criteria),
            "qaHooks": list(self.qa_hooks),
            "phase": self.phase,
            "priority": self.priority,
            "status": self.status,
            "estimatedDuration": self.estimated_duration,
            "tags": list(self.tags),
            "version": self.version,
            "children": [child.to_dict() for child in self.children],
        }

    def iter_steps(self) -> Iterator["PlanStep"]:
        """Yield this plan step and all descendants depth-first."""

        yield self
        for child in self.children:
            yield from child.iter_steps()

    def to_qa_checklist(self) -> List[Dict[str, object]]:
        """Return QA checklist entries for the step hierarchy."""

        checklist: List[Dict[str, object]] = []
        for step in self.iter_steps():
            checklist.append(
                {
                    "macro": step.macro,
                    "ownerAgent": step.owner_agent,
                    "description": step.description,
                    "outcomes": list(step.outcomes),
                    "acceptanceCriteria": list(step.acceptance_criteria),
                    "qaHooks": list(step.qa_hooks),
                    "phase": step.phase,
                    "priority": step.priority,
                    "status": step.status,
                    "estimatedDuration": step.estimated_duration,
                    "tags": list(step.tags),
                    "version": step.version,
                }
            )
        return checklist

    def to_manifest(self) -> Dict[str, object]:
        """Produce a flattened orchestration manifest for the Meta Agent."""

        tasks: List[Dict[str, object]] = []

        def _collect(step: "PlanStep", parent: Optional[str]) -> None:
            tasks.append(
                {
                    "macro": step.macro,
                    "ownerAgent": step.owner_agent,
                    "description": step.description,
                    "outcomes": list(step.outcomes),
                    "acceptanceCriteria": list(step.acceptance_criteria),
                    "qaHooks": list(step.qa_hooks),
                    "phase": step.phase,
                    "priority": step.priority,
                    "status": step.status,
                    "estimatedDuration": step.estimated_duration,
                    "tags": list(step.tags),
                    "version": step.version,
                    "dependsOn": [parent] if parent else [],
                }
            )
            for child in step.children:
                _collect(child, step.macro)

        _collect(self, None)
        return {"root": self.macro, "tasks": tasks}

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
