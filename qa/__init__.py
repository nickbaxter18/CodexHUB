"""
SECTION: Header & Purpose
    - Exposes QA-related modules and value objects as a cohesive package for importers.

SECTION: Imports / Dependencies
    - Imports the primary QA engine components for convenience re-exporting.

SECTION: Exports / Public API
    - ``qa_engine`` and ``qa_event_bus`` modules alongside ``QAEvaluation``, ``QAEngine``, ``QARules``, and ``QAEventBus``.
"""

from .qa_engine import (
    MacroValidationResult,
    MetricPolicy,
    MetricViolation,
    QAEvaluation,
    QAEngine,
    QARules,
    RemediationPlan,
)
from .qa_event_bus import QAEventBus

__all__ = [
    "qa_engine",
    "qa_event_bus",
    "MacroValidationResult",
    "MetricPolicy",
    "MetricViolation",
    "QAEvaluation",
    "QAEngine",
    "QARules",
    "RemediationPlan",
    "QAEventBus",
]
