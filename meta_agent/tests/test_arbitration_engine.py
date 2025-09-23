"""ArbitrationEngine conflict resolution tests."""

# === Imports / Dependencies ===
from __future__ import annotations

from meta_agent.arbitration_engine import ArbitrationDecision, ArbitrationEngine


# === Tests ===

def test_resolve_conflict_with_priority() -> None:
    """Higher governance priority should outweigh raw trust."""

    engine = ArbitrationEngine()
    engine.governance.get_priority = lambda metric, agent: {"A": 1.5, "B": 1.0}.get(agent, 1.0)
    conflicts = [
        {"agent": "A", "metric": "latency"},
        {"agent": "B", "metric": "latency"},
    ]
    decision = engine.resolve_conflict(conflicts, {"A": 1.0, "B": 1.2})
    assert isinstance(decision, ArbitrationDecision)
    assert decision.winner == "A"
    assert decision.rationale["method"] == "trust_priority_weighting"


def test_default_agent_on_empty_conflicts() -> None:
    """Missing conflicts should resolve to the neutral "unknown" agent."""

    engine = ArbitrationEngine()
    decision = engine.resolve_conflict([], {"A": 1.0})
    assert decision.winner == "unknown"


def test_collect_ready_conflicts_after_stale_timeout() -> None:
    """Single events should resolve once the staleness horizon is exceeded."""

    engine = ArbitrationEngine(stale_after=0.0)
    engine.add_event({"agent": "solo", "metric": "uptime"})
    conflicts = engine.collect_ready_conflicts("uptime")
    assert conflicts, "Stale single event should be returned for resolution"
    assert conflicts[0]["agent"] == "solo"
    assert "event_id" in conflicts[0]
