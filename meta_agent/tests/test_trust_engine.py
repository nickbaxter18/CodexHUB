"""Tests for TrustEngine persistence and Bayesian updates."""

# === Imports / Dependencies ===
from __future__ import annotations

from pathlib import Path

from meta_agent.trust_engine import TrustEngine


# === Tests ===


def test_initial_load_empty(tmp_path: Path) -> None:
    """TrustEngine should start with no scores when storage is empty."""

    path = tmp_path / "trust.json"
    engine = TrustEngine(path)
    assert engine.trust_scores == {}


def test_record_failure_and_success(tmp_path: Path) -> None:
    """Failures reduce trust while successes increase it with bounds applied."""

    path = tmp_path / "trust.json"
    engine = TrustEngine(path)
    engine.record_failure("agent-A")
    assert engine.trust_scores["agent-A"] == 0.9
    engine.record_success("agent-A")
    assert engine.trust_scores["agent-A"] > 0.9


def test_persistence(tmp_path: Path) -> None:
    """Trust scores persist across engine restarts."""

    path = tmp_path / "trust.json"
    engine = TrustEngine(path)
    engine.record_failure("agent-A")
    engine = TrustEngine(path)
    assert "agent-A" in engine.trust_scores


def test_flush_compacts_journal(tmp_path: Path) -> None:
    """Explicit flush should persist snapshot and clear the journal."""

    path = tmp_path / "trust.json"
    engine = TrustEngine(path, flush_interval=100)
    engine.record_failure("agent-A")
    assert engine.journal_path.exists()
    engine.flush()
    assert path.exists()
    assert not engine.journal_path.exists()
