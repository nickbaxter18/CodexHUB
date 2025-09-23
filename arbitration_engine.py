"""Arbitration logic for reconciling conflicting agent judgments."""

# === Imports / Dependencies ===
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qa_rules_loader import load_governance_rules


# === Types, Interfaces, Contracts, Schema ===
@dataclass
class _PendingEvent:
    event: Dict[str, Any]
    received_at: float
    event_id: str


@dataclass
class ArbitrationDecision:
    metric: str
    winner: str
    participants: List[Dict[str, Any]]
    rationale: Dict[str, Any]


class ArbitrationEngine:
    """Coordinate arbitration decisions using trust scores and governance priorities."""

    def __init__(self, stale_after: float = 30.0, max_queue: int = 50) -> None:
        self.pending_events: Dict[str, List[_PendingEvent]] = {}
        self.governance = load_governance_rules()
        self._stale_after = stale_after
        self._max_queue = max_queue

    def add_event(self, event: Dict[str, Any]) -> None:
        """Queue ``event`` for later conflict resolution grouped by metric."""

        metric = event.get("metric")
        if not metric:
            return
        queue = self.pending_events.setdefault(metric, [])
        agent = event.get("agent")
        if agent:
            queue[:] = [pending for pending in queue if pending.event.get("agent") != agent]
        queue.append(_PendingEvent(event=dict(event), received_at=time.monotonic(), event_id=str(uuid.uuid4())))
        if len(queue) > self._max_queue:
            queue.pop(0)

    def collect_ready_conflicts(self, metric: str, now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Retrieve queued events when conflicts are ready for resolution."""

        queue = self.pending_events.get(metric)
        if not queue:
            return []
        current_time = time.monotonic() if now is None else now
        if len(queue) >= 2 or current_time - queue[0].received_at >= self._stale_after:
            self.pending_events.pop(metric, None)
            ready: List[Dict[str, Any]] = []
            for pending in queue:
                event_copy = dict(pending.event)
                event_copy.setdefault("event_id", pending.event_id)
                ready.append(event_copy)
            return ready
        return []

    def resolve_conflict(
        self,
        conflicts: List[Dict[str, Any]],
        trust_scores: Dict[str, float],
    ) -> ArbitrationDecision:
        """Return a structured arbitration decision for the conflicting events."""

        if not conflicts:
            return ArbitrationDecision(
                metric="unknown",
                winner="unknown",
                participants=[],
                rationale={"reason": "no_conflicts"},
            )
        metric = next((event.get("metric") for event in conflicts if event.get("metric")), "unknown")
        scores: List[Dict[str, Any]] = []
        for event in conflicts:
            agent = event.get("agent") or "unknown"
            trust = float(trust_scores.get(agent, 1.0))
            priority = float(self.governance.get_priority(metric, agent))
            weight = trust * priority
            scores.append({
                "agent": agent,
                "trust": trust,
                "priority": priority,
                "weight": weight,
            })
        sorted_scores = sorted(scores, key=lambda item: item["weight"], reverse=True)
        winner = sorted_scores[0]["agent"] if sorted_scores else conflicts[0].get("agent", "unknown")
        runner_up_weight = sorted_scores[1]["weight"] if len(sorted_scores) > 1 else 0.0
        top_weight = sorted_scores[0]["weight"] if sorted_scores else 0.0
        confidence = 0.0
        if top_weight + runner_up_weight > 0:
            confidence = (top_weight - runner_up_weight) / (top_weight + runner_up_weight)
        rationale = {
            "method": "trust_priority_weighting",
            "scores": sorted_scores,
            "confidence": max(confidence, 0.0),
            "participant_count": len(conflicts),
        }
        return ArbitrationDecision(
            metric=metric,
            winner=winner,
            participants=[dict(event) for event in conflicts],
            rationale=rationale,
        )


# === Error & Edge Case Handling ===
# Missing metrics or agent identifiers are ignored, and stale events resolve after ``stale_after`` seconds.
# Duplicate agent entries replace older events to avoid runaway queues.


# === Performance / Resource Considerations ===
# Conflicts are resolved using a simple linear scan, sufficient for tens of agents per metric. Queue size is
# capped to avoid unbounded memory growth, and stale events ensure eventual decisions.


# === Exports / Public API ===
__all__ = ["ArbitrationEngine", "ArbitrationDecision"]
