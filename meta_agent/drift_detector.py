"""Robust statistical drift detection with PSI, KS, and KL divergence metrics."""

# === Header & Purpose ===
# Implements governance-grade drift detection that converts QA event streams into
# statistical evidence. Sliding windows of numeric outcomes are compared against
# reference distributions using Population Stability Index (PSI), Kolmogorov-
# Smirnov (KS) tests, and Kullback-Leibler (KL) divergence. Operational drift
# caused by repeated failures or disabled tests remains supported for backwards
# compatibility, ensuring deterministic governance proposals with actionable
# metadata.

# === Imports / Dependencies ===
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import (
    Any,
    Deque,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
)

import numpy as np


# === Types, Interfaces, Contracts ===
@dataclass(frozen=True)
class DriftMetricThresholds:
    """Thresholds required for a metric to be considered within governance bounds."""

    psi: float
    ks: float
    kl: float


@dataclass
class MetricProfile:
    """Reference distribution and enforcement metadata for a single metric."""

    name: str
    reference_values: np.ndarray
    thresholds: DriftMetricThresholds
    bins: np.ndarray
    reference_counts: np.ndarray
    reference_probabilities: np.ndarray
    unit: Optional[str] = None

    @classmethod
    def from_config(
        cls,
        name: str,
        config: Mapping[str, Any],
        epsilon: float,
        *,
        max_bins: int = 20,
    ) -> "MetricProfile":
        """Construct a profile from configuration payloads."""

        values = np.asarray(config.get("reference_values", []), dtype=float)
        if values.size == 0:
            raise ValueError(f"Metric '{name}' requires non-empty reference_values")
        raw_bins = config.get("bins")
        if raw_bins:
            bins = np.asarray(raw_bins, dtype=float)
        else:
            # Use numpy heuristics bounded by ``max_bins`` for stability.
            suggested_bins = int(np.clip(np.sqrt(values.size), 5, max_bins))
            bins = np.histogram_bin_edges(values, bins=suggested_bins)
        if bins.ndim != 1 or bins.size < 2:
            raise ValueError(f"Metric '{name}' bins must contain at least two edges")
        counts, _ = np.histogram(values, bins=bins)
        probabilities = MetricProfile._to_probabilities(counts, epsilon)
        thresholds = DriftMetricThresholds(
            psi=float(config.get("psi_threshold", 0.0)),
            ks=float(config.get("ks_threshold", 0.0)),
            kl=float(config.get("kl_threshold", 0.0)),
        )
        return cls(
            name=name,
            reference_values=values,
            thresholds=thresholds,
            bins=bins,
            reference_counts=counts,
            reference_probabilities=probabilities,
            unit=str(config.get("unit")) if config.get("unit") else None,
        )

    @staticmethod
    def _to_probabilities(counts: np.ndarray, epsilon: float) -> np.ndarray:
        total = float(np.sum(counts))
        if total <= 0.0:
            # Uniform smoothing avoids divide-by-zero and keeps PSI stable.
            return np.full_like(counts, 1.0 / counts.size, dtype=float)
        smoothed = counts.astype(float) + epsilon
        return smoothed / np.sum(smoothed)


@dataclass
class DriftReport:
    """Structured result describing statistical drift for a metric."""

    metric: str
    psi: float
    ks: float
    kl: float
    sample_size: int
    thresholds: DriftMetricThresholds
    failing_metrics: List[str] = field(default_factory=list)
    drift_detected: bool = False
    unit: Optional[str] = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DriftAlert:
    """Internal record describing why drift escalation was triggered."""

    metric: str
    agent: Optional[str]
    report: Optional[DriftReport]
    status_summary: Dict[str, int] = field(default_factory=dict)
    triggered_by_status: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class DriftDetector:
    """Monitor QA outcomes and raise governance amendments when drift occurs."""

    def __init__(
        self,
        window_size: int = 50,
        threshold: int = 3,
        *,
        metric_configs: Optional[Mapping[str, Mapping[str, Any]]] = None,
        min_samples: int = 30,
        epsilon: float = 1e-6,
    ) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        if min_samples <= 0:
            raise ValueError("min_samples must be positive")
        self.window_size = window_size
        self.status_threshold = threshold
        self.min_samples = min_samples
        self._epsilon = float(epsilon)
        self._profiles: Dict[str, MetricProfile] = {}
        if metric_configs:
            for name, config in metric_configs.items():
                self._profiles[name] = MetricProfile.from_config(name, config, self._epsilon)
        self._status_history: MutableMapping[Tuple[str, str], Deque[str]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )
        self._live_windows: Dict[str, Deque[float]] = {
            name: deque(maxlen=self.window_size) for name in self._profiles
        }
        self._reports: Dict[str, DriftReport] = {}
        self._proposals: List[Dict[str, Any]] = []
        self._last_alert: Optional[DriftAlert] = None

    def record_event(
        self,
        agent: Optional[str],
        metric: Optional[str],
        status: str,
        *,
        value: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> None:
        """Record a QA event outcome for drift evaluation."""

        if not metric:
            return
        normalized_status = (status or "unknown").strip().lower()
        status_summary: Dict[str, int] = {}
        if agent:
            history = self._status_history[(agent, metric)]
            history.append(normalized_status)
            status_summary = {
                "fail_count": history.count("fail"),
                "disabled_count": history.count("disabled"),
                "total": len(history),
            }
        triggered_status = bool(agent) and (
            status_summary.get("fail_count", 0) >= self.status_threshold
            or status_summary.get("disabled_count", 0) >= self.status_threshold
        )
        report: Optional[DriftReport] = None
        if value is not None:
            window = self._live_windows.setdefault(metric, deque(maxlen=self.window_size))
            window.append(float(value))
            report = self._evaluate_metric(metric, window)
        elif metric in self._reports:
            report = self._reports[metric]
        if triggered_status or (report and report.drift_detected):
            metadata: Dict[str, Any] = {}
            if threshold is not None:
                metadata["threshold"] = float(threshold)
            if value is not None:
                metadata["latest_value"] = float(value)
            self._last_alert = DriftAlert(
                metric=metric,
                agent=agent,
                report=report,
                status_summary=status_summary,
                triggered_by_status=triggered_status,
                metadata=metadata,
            )

    def is_drift(self) -> bool:
        """Return ``True`` when statistical or operational drift is active."""

        if self._last_alert and (
            self._last_alert.triggered_by_status
            or (self._last_alert.report and self._last_alert.report.drift_detected)
        ):
            return True
        for metric, window in list(self._live_windows.items()):
            report = self._evaluate_metric(metric, window)
            if report and report.drift_detected:
                self._last_alert = DriftAlert(
                    metric=metric,
                    agent=None,
                    report=report,
                    status_summary={},
                    triggered_by_status=False,
                )
                return True
        for (agent, metric), history in self._status_history.items():
            fail_count = history.count("fail")
            disabled_count = history.count("disabled")
            if fail_count >= self.status_threshold or disabled_count >= self.status_threshold:
                self._last_alert = DriftAlert(
                    metric=metric,
                    agent=agent,
                    report=self._reports.get(metric),
                    status_summary={
                        "fail_count": fail_count,
                        "disabled_count": disabled_count,
                        "total": len(history),
                    },
                    triggered_by_status=True,
                )
                return True
        return False

    def propose_amendment(self) -> Dict[str, Any]:
        """Return a governance amendment proposal describing the observed drift."""

        if self._last_alert is None and not self.is_drift():
            raise RuntimeError("no drift detected to propose amendment")
        alert = self._last_alert
        if alert is None:
            raise RuntimeError("drift alert context missing")
        report = alert.report
        failing_metrics = report.failing_metrics if report else []
        severity = self._derive_severity(alert, failing_metrics)
        statistics: Dict[str, Any] = {}
        if report:
            statistics = {
                "psi": report.psi,
                "ks": report.ks,
                "kl": report.kl,
                "thresholds": {
                    "psi": report.thresholds.psi,
                    "ks": report.thresholds.ks,
                    "kl": report.thresholds.kl,
                },
                "sample_size": report.sample_size,
                "unit": report.unit,
                "failing_metrics": failing_metrics,
                "generated_at": report.generated_at.isoformat(),
            }
        proposal = {
            "action": "review",
            "reason": "statistical_drift" if failing_metrics else "operational_drift",
            "agent": alert.agent,
            "metric": alert.metric,
            "severity": severity,
            "status_summary": alert.status_summary,
            "statistics": statistics,
            "window_size": self.window_size,
            "status_threshold": self.status_threshold,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "recommended_documents": ["QA.md", "GOVERNANCE.md", "META_AGENT.md"],
        }
        if alert.metadata:
            proposal["context"] = alert.metadata
        if not failing_metrics and not alert.triggered_by_status:
            proposal["reason"] = "manual_review"
        self._proposals.append(proposal)
        self._last_alert = None
        return proposal

    def get_proposals(self) -> List[Dict[str, Any]]:
        """Expose accumulated amendment proposals for auditing."""

        return list(self._proposals)

    def _evaluate_metric(self, metric: str, window: Iterable[float]) -> Optional[DriftReport]:
        profile = self._profiles.get(metric)
        if profile is None:
            return None
        values = np.asarray(list(window), dtype=float)
        if values.size < self.min_samples:
            return None
        psi = self._population_stability_index(profile, values)
        ks = self._kolmogorov_smirnov(profile.reference_values, values)
        kl = self._kullback_leibler(profile, values)
        failing: List[str] = []
        if psi > profile.thresholds.psi:
            failing.append("psi")
        if ks > profile.thresholds.ks:
            failing.append("ks")
        if kl > profile.thresholds.kl:
            failing.append("kl")
        report = DriftReport(
            metric=metric,
            psi=float(psi),
            ks=float(ks),
            kl=float(kl),
            sample_size=int(values.size),
            thresholds=profile.thresholds,
            failing_metrics=failing,
            drift_detected=bool(failing),
            unit=profile.unit,
        )
        self._reports[metric] = report
        return report

    def _population_stability_index(self, profile: MetricProfile, values: np.ndarray) -> float:
        live_counts, _ = np.histogram(values, bins=profile.bins)
        live_probabilities = MetricProfile._to_probabilities(live_counts, self._epsilon)
        ref_probabilities = profile.reference_probabilities
        delta = live_probabilities - ref_probabilities
        quotient = np.log(
            (live_probabilities + self._epsilon) / (ref_probabilities + self._epsilon)
        )
        return float(np.sum(delta * quotient))

    def _kullback_leibler(self, profile: MetricProfile, values: np.ndarray) -> float:
        live_counts, _ = np.histogram(values, bins=profile.bins)
        live_probabilities = MetricProfile._to_probabilities(live_counts, self._epsilon)
        ref_probabilities = profile.reference_probabilities
        quotient = np.log(
            (live_probabilities + self._epsilon) / (ref_probabilities + self._epsilon)
        )
        return float(np.sum(live_probabilities * quotient))

    def _kolmogorov_smirnov(self, reference: np.ndarray, live: np.ndarray) -> float:
        reference_sorted = np.sort(reference)
        live_sorted = np.sort(live)
        combined = np.concatenate([reference_sorted, live_sorted])
        combined.sort()
        ref_cdf = np.searchsorted(reference_sorted, combined, side="right") / reference_sorted.size
        live_cdf = np.searchsorted(live_sorted, combined, side="right") / live_sorted.size
        return float(np.max(np.abs(live_cdf - ref_cdf)))

    def _derive_severity(self, alert: DriftAlert, failing_metrics: Sequence[str]) -> str:
        fail_count = alert.status_summary.get("fail_count", 0)
        disabled_count = alert.status_summary.get("disabled_count", 0)
        if len(failing_metrics) >= 2 or fail_count >= self.status_threshold * 2:
            return "high"
        if fail_count >= self.status_threshold or disabled_count >= self.status_threshold:
            return "moderate"
        if failing_metrics:
            return "moderate"
        return "informational"


# === Error & Edge Case Handling ===
# - Unknown metrics fall back to operational drift detection without raising.
# - Empty or undersized sample windows short-circuit without computing metrics.
# - Logarithmic calculations are epsilon-smoothed to avoid division-by-zero.
# - ``propose_amendment`` raises ``RuntimeError`` when invoked without drift context.

# === Performance / Resource Considerations ===
# - Histograms and CDFs operate on numpy arrays for vectorised O(n) complexity.
# - Deques limit memory usage to ``window_size`` elements per metric/agent pair.

# === Exports / Public API ===
__all__ = ["DriftDetector", "DriftReport", "DriftMetricThresholds"]
