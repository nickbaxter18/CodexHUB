"""Sliding window drift detection for QA metrics and governance rules."""

# === Imports / Dependencies ===
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional, Tuple


# === Types, Interfaces, Contracts, Schema ===
class DriftDetector:
    """Track metric outcomes and flag repeated failures that suggest drift."""

    def __init__(self, window_size: int = 5, threshold: int = 3) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.window_size = window_size
        self.threshold = threshold
        self.history: Dict[Tuple[str, str], Deque[str]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )
        self._last_drift: Optional[Dict[str, Any]] = None
        self._proposals: List[Dict[str, Any]] = []

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
# Missing agent or metric identifiers are ignored. Invalid initialization parameters raise ``ValueError``.
# Proposals are only generated when drift metadata exists to avoid empty recommendations.


# === Performance / Resource Considerations ===
# Memory usage grows with ``window_size`` × number of (agent, metric) pairs. Operations are O(window_size).


# === Exports / Public API ===
__all__ = ["DriftDetector"]
