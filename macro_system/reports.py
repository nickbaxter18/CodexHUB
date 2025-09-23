"""Analytical helpers for auditing macro metadata coverage and readiness.

Header & Purpose:
    Provide utilities that inspect loaded macros to surface gaps ahead of QA/Meta
    Agent integrations.

Imports/Dependencies:
    * collections for counting ownership coverage.
    * dataclasses for structured reporting objects.
    * typing for type hints across the public API.

Types/Interfaces/Schemas:
    ``AgentCoverage`` summarises how many macros each agent owns.
    ``MetadataGaps`` lists macros lacking the metadata required by downstream
    agents.
    ``MacroReview`` composes the overall diagnostic payload returned to callers.

Core Logic/Implementation:
    ``generate_macro_review`` walks every macro, compiles coverage statistics,
    and returns actionable suggestions.

Error & Edge Handling:
    The helpers tolerate missing metadata by classifying those macros under
    "Unassigned" ownership and flagging them in the resulting report.

Performance Considerations:
    The operations are O(number of macros) and operate entirely in memory,
    which remains efficient for the current catalogue size.

Exports/Public API:
    ``generate_macro_review`` for consumers that need an actionable summary of
    the macro catalogue before orchestration.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Mapping

from .types import Macro

# === Types ===


@dataclass(frozen=True)
class AgentCoverage:
    """Number of macros owned by each agent."""

    total_macros: int
    per_agent: Mapping[str, int]


@dataclass(frozen=True)
class MetadataGaps:
    """Lists of macros missing critical metadata."""

    unassigned: List[str]
    missing_outcomes: List[str]
    missing_acceptance: List[str]
    missing_qa_hooks: List[str]
    default_outcomes: List[str]


@dataclass(frozen=True)
class MacroReview:
    """Structured review payload consumed by CLI and tests."""

    coverage: AgentCoverage
    gaps: MetadataGaps
    recommendations: List[str]


# === Implementation ===


def generate_macro_review(macros: Mapping[str, Macro]) -> MacroReview:
    """Inspect ``macros`` and return coverage statistics plus recommendations."""

    total = len(macros)
    ownership_counter: Counter[str] = Counter()
    unassigned: List[str] = []
    missing_outcomes: List[str] = []
    missing_acceptance: List[str] = []
    missing_qa_hooks: List[str] = []
    default_outcomes: List[str] = []

    for name, macro in macros.items():
        owner = macro.owner_agent or "Unassigned"
        ownership_counter[owner] += 1
        if macro.owner_agent is None:
            unassigned.append(name)
        if not macro.outcomes:
            missing_outcomes.append(name)
        elif _looks_like_default_outcome(macro.outcomes):
            default_outcomes.append(name)
        if not macro.acceptance_criteria:
            missing_acceptance.append(name)
        if not macro.qa_hooks:
            missing_qa_hooks.append(name)

    coverage = AgentCoverage(total_macros=total, per_agent=dict(sorted(ownership_counter.items())))
    gaps = MetadataGaps(
        unassigned=sorted(unassigned),
        missing_outcomes=sorted(missing_outcomes),
        missing_acceptance=sorted(missing_acceptance),
        missing_qa_hooks=sorted(missing_qa_hooks),
        default_outcomes=sorted(default_outcomes),
    )
    recommendations = _build_recommendations(coverage, gaps)

    return MacroReview(coverage=coverage, gaps=gaps, recommendations=recommendations)


# === Helper Functions ===


_DEFAULT_OUTCOME_MARKER = "Outputs are structured for downstream agent consumption."


def _looks_like_default_outcome(values: Iterable[str]) -> bool:
    """Return True if ``values`` are identical to the default migration payload."""

    values = list(values)
    if len(values) != 2:
        return False
    first, second = values
    return (
        isinstance(first, str)
        and "macro with actionable guidance" in first
        and isinstance(second, str)
        and second.strip() == _DEFAULT_OUTCOME_MARKER
    )


def _build_recommendations(coverage: AgentCoverage, gaps: MetadataGaps) -> List[str]:
    """Generate actionable follow-ups based on coverage and metadata gaps."""

    actions: List[str] = []

    if gaps.unassigned:
        actions.append(
            "Assign owner agents to all macros so Meta Agent can orchestrate hand-offs."
        )
    if gaps.missing_outcomes:
        actions.append(
            "Author macro-specific outcomes describing measurable deliverables."
        )
    if gaps.missing_acceptance:
        actions.append(
            "Provide acceptance criteria so QA Agent MD can score each macro."
        )
    if gaps.missing_qa_hooks:
        actions.append(
            "Attach qaHooks for every macro to wire automation entry points."
        )
    if gaps.default_outcomes:
        actions.append(
            "Replace default migration outcomes with detailed, agent-owned results."
        )
    if not actions:
        actions.append("Metadata coverage complete — proceed with QA/Meta integration.")

    return actions


# === Exports ===

__all__ = ["AgentCoverage", "MetadataGaps", "MacroReview", "generate_macro_review"]
