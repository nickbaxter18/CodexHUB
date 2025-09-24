"""Sliding window and statistical drift detection utilities."""

# === Imports / Dependencies ===
from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


# === Types, Interfaces, Contracts, Schema ===
@dataclass(frozen=True)
class DriftMetricResult:
    """Result for a single drift metric evaluation."""

    metric: str
    score: float
    threshold: float
    drift_detected: bool

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the metric result."""

        return {
            "metric": self.metric,
            "score": self.score,
            "threshold": self.threshold,
            "drift_detected": self.drift_detected,
        }


@dataclass(frozen=True)
class DriftReport:
    """Structured drift report containing metric-level outcomes."""

    results: List[DriftMetricResult] = field(default_factory=list)
    drift_detected: bool = False
    reference_size: int = 0
    live_size: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable dictionary view of the report."""

        return {
            "drift_detected": self.drift_detected,
            "metrics": [result.as_dict() for result in self.results],
            "reference_size": self.reference_size,
            "live_size": self.live_size,
            "details": dict(self.details),
        }


def _coerce_numeric(values: Iterable[float]) -> np.ndarray:
    """Return numeric, finite values from ``values`` as a NumPy array."""

    cleaned: List[float] = []
    for value in values:
        try:
            numeric = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            cleaned.append(numeric)
    return np.asarray(cleaned, dtype=float)


def _resolve_edges(reference: np.ndarray, live: np.ndarray, bins: int) -> np.ndarray:
    """Compute histogram edges covering both reference and live arrays."""

    bins = max(2, int(bins))
    if reference.size == 0 and live.size == 0:
        return np.linspace(0.0, 1.0, bins + 1)
    candidate_min = float(
        min(([reference.min()] if reference.size else []) + ([live.min()] if live.size else []))
    )
    candidate_max = float(
        max(([reference.max()] if reference.size else []) + ([live.max()] if live.size else []))
    )
    if candidate_min == candidate_max:
        candidate_min -= 0.5
        candidate_max += 0.5
    return np.linspace(candidate_min, candidate_max, bins + 1)


def population_stability_index(reference: np.ndarray, live: np.ndarray, bins: int) -> float:
    """Return the population stability index between ``reference`` and ``live``."""

    if reference.size == 0 or live.size == 0:
        return 0.0
    edges = _resolve_edges(reference, live, bins)
    ref_counts, _ = np.histogram(reference, bins=edges)
    live_counts, _ = np.histogram(live, bins=edges)
    total_ref = ref_counts.sum()
    total_live = live_counts.sum()
    if total_ref == 0 or total_live == 0:
        return 0.0
    epsilon = 1e-12
    expected = ref_counts / total_ref
    actual = live_counts / total_live
    ratio = (actual + epsilon) / (expected + epsilon)
    psi = np.sum((actual - expected) * np.log(ratio))
    return float(abs(psi))


def kolmogorov_smirnov_statistic(reference: np.ndarray, live: np.ndarray) -> float:
    """Return the Kolmogorov-Smirnov statistic for the two samples."""

    if reference.size == 0 or live.size == 0:
        return 0.0
    combined = np.concatenate([reference, live])
    combined.sort()
    ref_sorted = np.sort(reference)
    live_sorted = np.sort(live)
    ref_cdf = np.searchsorted(ref_sorted, combined, side="right") / ref_sorted.size
    live_cdf = np.searchsorted(live_sorted, combined, side="right") / live_sorted.size
    return float(np.max(np.abs(ref_cdf - live_cdf)))


def kl_divergence(reference: np.ndarray, live: np.ndarray, bins: int) -> float:
    """Return the KL divergence ``D_live||reference`` using shared histogram bins."""

    if reference.size == 0 or live.size == 0:
        return 0.0
    edges = _resolve_edges(reference, live, bins)
    ref_counts, _ = np.histogram(reference, bins=edges)
    live_counts, _ = np.histogram(live, bins=edges)
    total_ref = ref_counts.sum()
    total_live = live_counts.sum()
    if total_ref == 0 or total_live == 0:
        return 0.0
    epsilon = 1e-12
    ref_prob = (ref_counts + epsilon) / (total_ref + epsilon * len(ref_counts))
    live_prob = (live_counts + epsilon) / (total_live + epsilon * len(live_counts))
    divergence = float(np.sum(live_prob * np.log(live_prob / ref_prob)))
    return max(divergence, 0.0)


class DriftDetector:
    """Track metric outcomes and flag repeated failures or statistical drift."""

    def __init__(
        self,
        window_size: int = 5,
        threshold: int = 3,
        *,
        psi_threshold: float = 0.2,
        ks_threshold: float = 0.1,
        kl_threshold: float = 0.1,
        min_samples: int = 50,
        bin_count: int = 10,
    ) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        if min_samples <= 0:
            raise ValueError("min_samples must be positive")
        if bin_count < 2:
            raise ValueError("bin_count must be at least 2")
        self.window_size = window_size
        self.threshold = threshold
        self.min_samples = min_samples
        self.bin_count = bin_count
        self.history: Dict[Tuple[str, str], Deque[str]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )
        self._last_drift: Optional[Dict[str, Any]] = None
        self._last_report: Optional[DriftReport] = None
        self._proposals: List[Dict[str, Any]] = []
        self._distribution_thresholds = {
            "psi": float(psi_threshold),
            "ks": float(ks_threshold),
            "kl": float(kl_threshold),
        }

    def record_event(self, agent: Optional[str], metric: Optional[str], status: str) -> None:
        """Record ``status`` for ``agent`` and ``metric`` in the sliding window."""

        if not agent or not metric:
            return
        window = self.history[(agent, metric)]
        window.append(status)
        metadata = self._evaluate_window(agent, metric, window)
        if metadata:
            self._last_drift = metadata

    def detect_distribution_drift(
        self,
        reference: Sequence[float] | Iterable[float],
        live: Sequence[float] | Iterable[float],
        *,
        metric_name: str = "distribution",
    ) -> DriftReport:
        """Evaluate statistical drift using PSI, KS-test, and KL divergence."""

        ref_array = _coerce_numeric(reference)
        live_array = _coerce_numeric(live)
        details: Dict[str, Any] = {
            "min_samples": self.min_samples,
        }
        if ref_array.size < self.min_samples or live_array.size < self.min_samples:
            details.update(
                {
                    "insufficient_data": True,
                    "reference_size": int(ref_array.size),
                    "live_size": int(live_array.size),
                }
            )
            report = DriftReport([], False, int(ref_array.size), int(live_array.size), details)
            self._last_report = report
            return report

        bin_count = max(2, min(self.bin_count, int(ref_array.size), int(live_array.size)))
        details["bin_count"] = bin_count
        psi_score = population_stability_index(ref_array, live_array, bin_count)
        ks_score = kolmogorov_smirnov_statistic(ref_array, live_array)
        kl_score = kl_divergence(ref_array, live_array, bin_count)
        results = [
            self._build_metric_result("psi", psi_score),
            self._build_metric_result("ks", ks_score),
            self._build_metric_result("kl", kl_score),
        ]
        drift_detected = any(result.drift_detected for result in results)
        report = DriftReport(
            results,
            drift_detected,
            int(ref_array.size),
            int(live_array.size),
            details,
        )
        self._last_report = report
        if drift_detected:
            self._register_statistical_drift(metric_name, report)
        return report

    def is_drift(self) -> bool:
        """Return ``True`` when any tracked metric crosses the failure threshold."""

        if self._last_drift is not None:
            return True
        for (agent, metric), window in self.history.items():
            metadata = self._evaluate_window(agent, metric, window)
            if metadata:
                self._last_drift = metadata
                return True
        return False

    def propose_amendment(self) -> Dict[str, Any]:
        """Return a governance amendment proposal describing the observed drift."""

        if self._last_drift is None and not self.is_drift():
            raise RuntimeError("no drift detected to propose amendment")
        metadata = self._last_drift or {}
        reason = metadata.get("reason")
        if not reason:
            reason = (
                "distribution drift detected"
                if metadata.get("kind") == "statistical"
                else "repeated test failures"
            )
        proposal: Dict[str, Any] = {
            "action": "review",
            "reason": reason,
            "agent": metadata.get("agent"),
            "metric": metadata.get("metric"),
            "severity": metadata.get("severity", "moderate"),
            "fail_count": metadata.get("fail_count", 0),
            "disabled_count": metadata.get("disabled_count", 0),
            "window_size": self.window_size,
            "threshold": self.threshold,
            "recommended_documents": metadata.get(
                "documents", self._event_documents(metadata.get("disabled_count", 0))
            ),
            "correlation_hint": metadata.get("correlation_hint"),
        }
        if metadata.get("kind") == "statistical":
            proposal["recommended_documents"] = metadata.get(
                "documents", self._statistical_documents()
            )
            if self._last_report is not None:
                proposal["drift_metrics"] = self._last_report.as_dict()
        self._proposals.append(proposal)
        self._last_drift = None
        return proposal

    def get_proposals(self) -> List[Dict[str, Any]]:
        """Expose accumulated amendment proposals for auditing."""

        return list(self._proposals)

    def _build_metric_result(self, metric: str, score: float) -> DriftMetricResult:
        threshold = self._distribution_thresholds.get(metric, 0.0)
        return DriftMetricResult(metric, float(score), threshold, float(score) > threshold)

    def _register_statistical_drift(self, metric_name: str, report: DriftReport) -> None:
        severity = self._severity_from_report(report)
        metadata = {
            "kind": "statistical",
            "metric": metric_name,
            "severity": severity,
            "documents": self._statistical_documents(),
            "fail_count": 0,
            "disabled_count": 0,
            "correlation_hint": metric_name,
            "reason": "distribution drift detected",
        }
        if report.results:
            metadata["report"] = report.as_dict()
        self._last_drift = metadata

    def _severity_from_report(self, report: DriftReport) -> str:
        if not report.results:
            return "moderate"
        max_ratio = 0.0
        for result in report.results:
            if result.threshold <= 0:
                continue
            ratio = result.score / result.threshold
            if ratio > max_ratio:
                max_ratio = ratio
        if max_ratio >= 2.0:
            return "critical"
        if max_ratio >= 1.25:
            return "high"
        return "moderate"

    @staticmethod
    def _event_documents(disabled_count: int) -> List[str]:
        documents = ["QA.md"]
        if disabled_count > 0:
            documents.append("AGENTS.md")
        return documents

    @staticmethod
    def _statistical_documents() -> List[str]:
        return ["GOVERNANCE.md", "QA_ENGINE.md"]

    def _evaluate_window(
        self,
        agent: str,
        metric: str,
        window: Deque[str],
    ) -> Optional[Dict[str, Any]]:
        fail_count = window.count("fail")
        disabled_count = window.count("disabled")
        if fail_count >= self.threshold or disabled_count >= self.threshold:
            severity = "high" if fail_count >= self.threshold * 2 else "moderate"
            documents = self._event_documents(disabled_count)
            return {
                "kind": "event",
                "agent": agent,
                "metric": metric,
                "fail_count": fail_count,
                "disabled_count": disabled_count,
                "severity": severity,
                "documents": documents,
                "correlation_hint": f"{agent}:{metric}",
                "reason": "repeated test failures",
            }
        return None


# === Error & Edge Case Handling ===
# Missing agent or metric identifiers are ignored. Invalid initialization parameters raise ``ValueError``.
# Proposals are only generated when drift metadata exists to avoid empty recommendations.
# Statistical drift gracefully handles insufficient samples and non-numeric values.


# === Performance / Resource Considerations ===
# Memory usage grows with ``window_size`` × number of (agent, metric) pairs. Operations are O(window_size).
# Statistical evaluations rely on NumPy vectorisation for sub-second execution across thousands of samples.


# === Exports / Public API ===
__all__ = ["DriftDetector", "DriftReport", "DriftMetricResult"]
