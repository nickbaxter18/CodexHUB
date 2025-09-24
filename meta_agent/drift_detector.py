"""Sliding window and statistical drift detection for QA governance."""

# === Imports / Dependencies ===
from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Mapping, Optional, Sequence, Tuple


# === Types, Interfaces, Contracts, Schema ===
EPSILON = 1e-9
DEFAULT_THRESHOLDS: Dict[str, float] = {"psi": 0.2, "ks": 0.1, "kl": 0.5}


@dataclass(frozen=True)
class DriftMetricResult:
    """Summary of a single statistical drift metric evaluation."""

    metric: str
    score: float
    threshold: float
    drift_detected: bool
    details: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the metric result."""

        return {
            "metric": self.metric,
            "score": self.score,
            "threshold": self.threshold,
            "drift_detected": self.drift_detected,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class DriftReport:
    """Aggregated drift assessment across statistical metrics."""

    feature: str
    reference_size: int
    live_size: int
    metrics: Dict[str, DriftMetricResult]
    triggered: bool
    reason: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the drift report."""

        return {
            "feature": self.feature,
            "reference_size": self.reference_size,
            "live_size": self.live_size,
            "triggered": self.triggered,
            "reason": self.reason,
            "metrics": {name: metric.as_dict() for name, metric in self.metrics.items()},
        }


class DriftDetector:
    """Track metric outcomes and flag repeated failures that suggest drift."""

    def __init__(
        self,
        window_size: int = 5,
        threshold: int = 3,
        *,
        statistical_thresholds: Optional[Mapping[str, float]] = None,
        min_sample_size: int = 30,
        histogram_bins: int = 10,
    ) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        if min_sample_size <= 0:
            raise ValueError("min_sample_size must be positive")
        if histogram_bins < 2:
            raise ValueError("histogram_bins must be at least 2")
        self.window_size = window_size
        self.threshold = threshold
        self.history: Dict[Tuple[str, str], Deque[str]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )
        self._last_drift: Optional[Dict[str, Any]] = None
        self._proposals: List[Dict[str, Any]] = []
        self.min_sample_size = int(min_sample_size)
        self.histogram_bins = int(histogram_bins)
        configured_thresholds = {
            key: float(value)
            for key, value in (statistical_thresholds or {}).items()
            if key in DEFAULT_THRESHOLDS
        }
        self.thresholds: Dict[str, float] = {**DEFAULT_THRESHOLDS, **configured_thresholds}

    # === Sliding Window Drift Detection ===
    def record_event(self, agent: Optional[str], metric: Optional[str], status: str) -> None:
        """Record ``status`` for ``agent`` and ``metric`` in the sliding window."""

        if not agent or not metric:
            return
        window = self.history[(agent, metric)]
        window.append(status)
        metadata = self._evaluate_window(agent, metric, window)
        if metadata:
            self._last_drift = metadata

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
        proposal = {
            "action": "review",
            "reason": "repeated test failures",
            "agent": metadata.get("agent"),
            "metric": metadata.get("metric"),
            "severity": metadata.get("severity"),
            "fail_count": metadata.get("fail_count", 0),
            "disabled_count": metadata.get("disabled_count", 0),
            "window_size": self.window_size,
            "threshold": self.threshold,
            "recommended_documents": metadata.get("documents", ["QA.md"]),
            "correlation_hint": metadata.get("correlation_hint"),
        }
        self._proposals.append(proposal)
        self._last_drift = None
        return proposal

    def get_proposals(self) -> List[Dict[str, Any]]:
        """Expose accumulated amendment proposals for auditing."""

        return list(self._proposals)

    # === Statistical Drift Detection ===
    def detect_distribution_drift(
        self,
        reference_distribution: Sequence[float],
        live_distribution: Sequence[float],
        *,
        feature: str = "metric",
    ) -> DriftReport:
        """Compare ``reference_distribution`` with ``live_distribution`` for drift."""

        reference = self._sanitize_samples(reference_distribution)
        live = self._sanitize_samples(live_distribution)
        reference_size = len(reference)
        live_size = len(live)
        if reference_size < self.min_sample_size or live_size < self.min_sample_size:
            reason = (
                "insufficient samples"
                f" (reference={reference_size}, live={live_size}, required={self.min_sample_size})"
            )
            return DriftReport(
                feature=feature,
                reference_size=reference_size,
                live_size=live_size,
                metrics={},
                triggered=False,
                reason=reason,
            )

        edges = self._build_histogram_edges(reference, live)
        reference_counts = self._histogram_counts(reference, edges)
        live_counts = self._histogram_counts(live, edges)
        reference_probs = self._normalise(reference_counts)
        live_probs = self._normalise(live_counts)

        metrics: Dict[str, DriftMetricResult] = {}
        psi_score = self._population_stability_index(reference_probs, live_probs)
        metrics["psi"] = self._metric_result("psi", psi_score)
        kl_score = self._kl_divergence(reference_probs, live_probs)
        metrics["kl"] = self._metric_result("kl", kl_score)
        ks_score = self._ks_statistic(reference, live)
        metrics["ks"] = self._metric_result("ks", ks_score)

        triggered = any(result.drift_detected for result in metrics.values())
        return DriftReport(
            feature=feature,
            reference_size=reference_size,
            live_size=live_size,
            metrics=metrics,
            triggered=triggered,
        )

    # === Internal Helpers ===
    def _metric_result(self, metric: str, score: float) -> DriftMetricResult:
        threshold = self.thresholds.get(metric, DEFAULT_THRESHOLDS[metric])
        return DriftMetricResult(
            metric=metric,
            score=score,
            threshold=threshold,
            drift_detected=bool(score >= threshold),
            details={"threshold": threshold},
        )

    def _sanitize_samples(self, values: Sequence[float]) -> List[float]:
        sanitized: List[float] = []
        for value in values:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if math.isnan(numeric) or math.isinf(numeric):
                continue
            sanitized.append(numeric)
        return sanitized

    def _build_histogram_edges(
        self, reference: Sequence[float], live: Sequence[float]
    ) -> List[float]:
        combined = list(reference) + list(live)
        minimum = min(combined)
        maximum = max(combined)
        if minimum == maximum:
            return [minimum, minimum + 1.0]
        span = maximum - minimum
        step = span / float(self.histogram_bins)
        if step == 0:
            step = 1.0
        edges = [minimum + step * index for index in range(self.histogram_bins)]
        edges.append(maximum + step)
        return edges

    def _histogram_counts(self, values: Sequence[float], edges: Sequence[float]) -> List[float]:
        counts = [0.0 for _ in range(len(edges) - 1)]
        for value in values:
            for index in range(len(edges) - 1):
                upper_bound = edges[index + 1]
                if value < upper_bound or index == len(edges) - 2:
                    counts[index] += 1.0
                    break
        return counts

    def _normalise(self, counts: Sequence[float]) -> List[float]:
        total = sum(counts)
        if total == 0:
            return [0.0 for _ in counts]
        return [count / total for count in counts]

    def _population_stability_index(
        self, reference_probs: Sequence[float], live_probs: Sequence[float]
    ) -> float:
        psi = 0.0
        for reference, live in zip(reference_probs, live_probs):
            ref = reference if reference > 0 else EPSILON
            observed = live if live > 0 else EPSILON
            psi += (observed - ref) * math.log(observed / ref)
        return psi

    def _kl_divergence(
        self, reference_probs: Sequence[float], live_probs: Sequence[float]
    ) -> float:
        divergence = 0.0
        for reference, live in zip(reference_probs, live_probs):
            if reference <= 0:
                continue
            observed = live if live > 0 else EPSILON
            divergence += reference * math.log(reference / observed)
        return divergence

    def _ks_statistic(self, reference: Sequence[float], live: Sequence[float]) -> float:
        sorted_reference = sorted(reference)
        sorted_live = sorted(live)
        ref_size = len(sorted_reference)
        live_size = len(sorted_live)
        i = j = 0
        cdf_reference = 0.0
        cdf_live = 0.0
        ks_stat = 0.0
        while i < ref_size and j < live_size:
            if sorted_reference[i] <= sorted_live[j]:
                cdf_reference = (i + 1) / ref_size
                i += 1
            else:
                cdf_live = (j + 1) / live_size
                j += 1
            ks_stat = max(ks_stat, abs(cdf_reference - cdf_live))
        if i < ref_size:
            ks_stat = max(ks_stat, abs(1.0 - cdf_live))
        if j < live_size:
            ks_stat = max(ks_stat, abs(cdf_reference - 1.0))
        return ks_stat

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
            documents = ["QA.md"]
            if disabled_count >= self.threshold:
                documents.append("AGENTS.md")
            return {
                "agent": agent,
                "metric": metric,
                "fail_count": fail_count,
                "disabled_count": disabled_count,
                "severity": severity,
                "documents": documents,
                "correlation_hint": f"{agent}:{metric}",
            }
        return None


# === Error & Edge Case Handling ===
# - Missing agent or metric identifiers are ignored for sliding window detection.
# - Statistical drift detection sanitises NaNs/Infs and enforces minimum sample sizes.
# - Histogram bins default to 10 but can be configured for finer granularity.


# === Performance / Resource Considerations ===
# - Sliding window operations remain O(window_size).
# - Statistical calculations rely on simple Python loops and avoid heavy dependencies.


# === Exports / Public API ===
__all__ = ["DriftDetector", "DriftMetricResult", "DriftReport"]
