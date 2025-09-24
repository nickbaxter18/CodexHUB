"""Unit tests for MacroDependencyManager compatibility orchestration."""

# === Imports / Dependencies ===
from __future__ import annotations

import pytest

from pathlib import Path

from meta_agent.macro_dependency_manager import MacroDependencyManager


# === Tests ===


def test_register_macro_blocks_until_dependency_known() -> None:
    """Macros should be blocked until dependencies have known schemas."""

    manager = MacroDependencyManager()
    state = manager.register_macro("analytics", "1.0", {"catalog": "2.0"})
    assert state.blocked
    assert state.reason == "dependency catalog schema unknown"
    assert manager.get_blocked_macros()["analytics"] == state.reason
    assert "initialized_at" in state.diff


def test_dependency_updates_toggle_block_state() -> None:
    """Dependency schema updates should unblock or re-block macros based on compatibility."""

    manager = MacroDependencyManager()
    manager.register_macro("analytics", "1.0", {"catalog": "2.0"})
    updates = manager.update_dependency_schema("catalog", "2.0")
    assert updates and updates[-1].blocked is False
    assert updates[-1].diff["blocked"]["after"] is False
    assert manager.is_blocked("analytics") is False

    updates = manager.update_dependency_schema("catalog", "3.0")
    assert updates and updates[-1].blocked is True
    assert "schema mismatch" in (updates[-1].reason or "")
    assert manager.get_block_reason("analytics") == updates[-1].reason


def test_persistence_round_trip(tmp_path: Path) -> None:
    """Manager should persist macro state and dependency versions to disk."""

    storage = tmp_path / "macros.json"
    manager = MacroDependencyManager(storage)
    manager.register_macro("analytics", "1.0", {"catalog": "2.0"})
    manager.update_dependency_schema("catalog", "2.0")

    reloaded = MacroDependencyManager(storage)
    assert reloaded.is_blocked("analytics") is False
    state = reloaded.get_state("analytics")
    assert state.dependencies["catalog"] == "2.0"


def test_register_macro_requires_name() -> None:
    """Attempting to register an unnamed macro should raise a validation error."""

    manager = MacroDependencyManager()
    with pytest.raises(ValueError):
        manager.register_macro("", "1.0", {})


# === Performance / Resource Considerations ===
# Tests cover only logical correctness; performance characteristics are validated indirectly via targeted evaluations.
