"""Tests for DriftDetector sliding window drift logic."""

# === Imports / Dependencies ===
from __future__ import annotations

import numpy as np

from meta_agent.drift_detector import DriftDetector


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


def test_distribution_drift_detects_shift() -> None:
    """Distributional drift should generate a proposal with metric details."""

    detector = DriftDetector(
        window_size=3,
        threshold=2,
        psi_threshold=0.05,
        ks_threshold=0.05,
        kl_threshold=0.01,
        min_samples=30,
    )
    rng = np.random.default_rng(42)
    reference = rng.normal(loc=0.0, scale=1.0, size=300)
    live = rng.normal(loc=2.5, scale=1.0, size=300)
    report = detector.detect_distribution_drift(reference, live, metric_name="latency")
    assert report.drift_detected
    assert any(result.metric == "psi" and result.drift_detected for result in report.results)
    proposal = detector.propose_amendment()
    assert proposal["metric"] == "latency"
    assert proposal["reason"] == "distribution drift detected"
    assert proposal["recommended_documents"] == ["GOVERNANCE.md", "QA_ENGINE.md"]
    metrics_payload = proposal.get("drift_metrics", {})
    assert metrics_payload.get("drift_detected") is True
    assert metrics_payload.get("reference_size") == 300
    assert metrics_payload.get("live_size") == 300


def test_distribution_drift_respects_min_samples() -> None:
    """Insufficient data should not trigger drift and should provide context."""

    detector = DriftDetector(min_samples=10)
    report = detector.detect_distribution_drift([1.0, 1.1], [1.5, 1.6], metric_name="quality")
    assert report.drift_detected is False
    assert report.details.get("insufficient_data") is True
    assert report.details.get("reference_size") == 2
    assert report.details.get("live_size") == 2


def test_distribution_drift_handles_similar_distributions() -> None:
    """Similar distributions with relaxed thresholds should not flag drift."""

    detector = DriftDetector(
        psi_threshold=1.0,
        ks_threshold=1.0,
        kl_threshold=1.0,
        min_samples=20,
    )
    rng = np.random.default_rng(123)
    reference = rng.normal(loc=0.0, scale=1.0, size=200)
    live = rng.normal(loc=0.1, scale=1.05, size=200)
    report = detector.detect_distribution_drift(reference, live, metric_name="latency")
    assert report.drift_detected is False
    assert all(result.drift_detected is False for result in report.results)
