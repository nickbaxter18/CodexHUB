"""Tests for governance-grade statistical drift detection."""

# === Imports / Dependencies ===
from __future__ import annotations

from typing import Dict, Iterable

from meta_agent.drift_detector import DriftDetector


# === Helpers ===


def build_detector(config: Dict[str, Dict[str, float]], *, min_samples: int = 5) -> DriftDetector:
    """Construct a detector with deterministic configuration for tests."""

    return DriftDetector(
        window_size=20,
        threshold=3,
        metric_configs=config,
        min_samples=min_samples,
    )


def latency_config(
    *, psi_threshold: float = 0.15, ks_threshold: float = 0.1, kl_threshold: float = 0.4
) -> Dict[str, Dict[str, float]]:
    """Provide a latency configuration with clear separation between states."""

    return {
        "latency": {
            "psi_threshold": psi_threshold,
            "ks_threshold": ks_threshold,
            "kl_threshold": kl_threshold,
            "reference_values": [
                210.0,
                215.0,
                220.0,
                225.0,
                230.0,
                232.0,
                234.0,
                236.0,
                238.0,
                240.0,
            ],
            "unit": "milliseconds",
        }
    }


def stream(detector: DriftDetector, values: Iterable[float], *, status: str = "pass") -> None:
    """Push values into the detector for a single agent/metric."""

    for value in values:
        detector.record_event("qa", "latency", status, value=value, threshold=250.0)


# === Tests ===


def test_statistical_drift_detected_when_thresholds_exceeded() -> None:
    """Significant distribution shift should trigger statistical drift reporting."""

    detector = build_detector(latency_config())
    stream(detector, [320.0, 325.0, 330.0, 335.0, 340.0, 345.0], status="pass")
    assert detector.is_drift(), "Expected statistical drift for shifted latency distribution"
    proposal = detector.propose_amendment()
    assert proposal["reason"] == "statistical_drift"
    stats = proposal["statistics"]
    assert "psi" in stats["failing_metrics"]
    assert "ks" in stats["failing_metrics"]


def test_no_drift_when_distribution_matches_reference() -> None:
    """Values aligned with reference distribution should not trigger drift."""

    config = latency_config(psi_threshold=0.5, ks_threshold=0.5, kl_threshold=1.0)
    reference_values = config["latency"]["reference_values"]
    detector = build_detector(config, min_samples=len(reference_values))
    stream(detector, reference_values, status="pass")
    assert detector.is_drift() is False


def test_operational_drift_triggers_without_values() -> None:
    """Repeated failures without numeric values should still trigger drift."""

    detector = build_detector({}, min_samples=1)
    for _ in range(3):
        detector.record_event("qa", "latency", "fail")
    assert detector.is_drift()
    proposal = detector.propose_amendment()
    assert proposal["reason"] == "operational_drift"
    assert proposal["status_summary"]["fail_count"] >= 3


def test_proposals_accumulate_for_audit_trail() -> None:
    """Proposals returned by the detector should be stored for auditing."""

    detector = build_detector(latency_config())
    stream(detector, [320.0, 325.0, 330.0, 335.0, 340.0, 345.0])
    assert detector.is_drift()
    first = detector.propose_amendment()
    assert detector.get_proposals() == [first]
