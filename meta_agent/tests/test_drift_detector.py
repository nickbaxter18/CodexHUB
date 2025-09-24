"""Tests for DriftDetector sliding window drift logic."""

# === Imports / Dependencies ===
from __future__ import annotations

from meta_agent.drift_detector import DriftDetector, DriftReport


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


def test_distribution_drift_detects_large_shift() -> None:
    """Statistical drift detection should flag significant distribution changes."""

    detector = DriftDetector(
        window_size=3,
        threshold=2,
        statistical_thresholds={"psi": 0.05, "ks": 0.2, "kl": 0.05},
        min_sample_size=20,
        histogram_bins=5,
    )
    reference = [1.0, 1.2, 0.9, 1.1] * 10
    live = [2.5, 2.6, 2.7, 2.8, 3.0] * 8
    report = detector.detect_distribution_drift(reference, live, feature="latency")
    assert isinstance(report, DriftReport)
    assert report.triggered is True
    assert report.metrics["psi"].drift_detected is True
    assert report.metrics["ks"].drift_detected is True
    assert report.metrics["kl"].drift_detected is True


def test_distribution_drift_respects_sample_threshold() -> None:
    """Insufficient sample counts should disable statistical drift decisions."""

    detector = DriftDetector(min_sample_size=50)
    reference = [1.0] * 10
    live = [1.0] * 10
    report = detector.detect_distribution_drift(reference, live, feature="latency")
    assert report.triggered is False
    assert report.reason is not None
    assert report.metrics == {}


def test_distribution_drift_sanitises_invalid_values() -> None:
    """NaN and infinite values should be removed prior to statistical analysis."""

    detector = DriftDetector(min_sample_size=4, histogram_bins=3)
    reference = [1.0, float("nan"), 1.5, float("inf"), 0.8, 1.2]
    live = [1.1, 1.0, 0.9, 1.2, float("nan"), 1.3]
    report = detector.detect_distribution_drift(reference, live, feature="stability")
    assert report.reference_size == 4
    assert report.live_size == 5
    assert report.reason is None
