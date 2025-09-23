"""Tests for DriftDetector sliding window drift logic."""

# === Imports / Dependencies ===
from __future__ import annotations

from drift_detector import DriftDetector


# === Tests ===

def test_is_drift_detects_repeated_failures() -> None:
    """Two failures within the window should trigger drift detection."""

    detector = DriftDetector(window_size=3, threshold=2)
    detector.record_event("agent-A", "latency", "fail")
    detector.record_event("agent-A", "latency", "fail")
    assert detector.is_drift()


def test_no_drift_with_insufficient_fails() -> None:
    """Single failure must not trigger drift when threshold requires more."""

    detector = DriftDetector(window_size=3, threshold=2)
    detector.record_event("agent-A", "latency", "fail")
    assert not detector.is_drift()


def test_propose_without_drift_raises() -> None:
    """Requesting an amendment without drift should raise an error."""

    detector = DriftDetector(window_size=3, threshold=2)
    try:
        detector.propose_amendment()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError when proposing without drift")


def test_propose_amendment_contains_context() -> None:
    """Amendment proposals should include agent and metric context."""

    detector = DriftDetector(window_size=3, threshold=2)
    detector.record_event("agent-A", "latency", "fail")
    detector.record_event("agent-A", "latency", "fail")
    assert detector.is_drift()
    proposal = detector.propose_amendment()
    assert proposal["action"] == "review"
    assert proposal["agent"] == "agent-A"
    assert proposal["metric"] == "latency"
    assert proposal["severity"] in {"moderate", "high"}
    assert proposal["fail_count"] >= 2
    assert "QA.md" in proposal["recommended_documents"]


def test_disabled_events_request_agents_doc() -> None:
    """Repeated disables should reference AGENTS.md for remediation guidance."""

    detector = DriftDetector(window_size=3, threshold=2)
    detector.record_event("agent-A", "availability", "disabled")
    detector.record_event("agent-A", "availability", "disabled")
    assert detector.is_drift()
    proposal = detector.propose_amendment()
    assert "AGENTS.md" in proposal["recommended_documents"]
