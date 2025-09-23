"""Header & Purpose: verify macro_system routes through the Macros package."""

from __future__ import annotations

# === Imports / Dependencies ===
import importlib
from typing import Dict

import pytest

# === Types / Interfaces / Schemas ===
AliasExpectation = Dict[str, str]


# === Core Logic / Implementation ===
ALIASES: AliasExpectation = {
    "macro_system.cli": "macro_system.Macros.cli",
    "macro_system.engine": "macro_system.Macros.engine",
    "macro_system.macros": "macro_system.Macros.catalog",
    "macro_system.orchestrator": "macro_system.Macros.orchestrator",
    "macro_system.planner": "macro_system.Macros.planner",
    "macro_system.types": "macro_system.Macros.types",
}


@pytest.mark.parametrize("alias,target", sorted(ALIASES.items()))
def test_alias_modules_match_macros_package(alias: str, target: str) -> None:
    """Ensure each legacy module points to the consolidated Macros module."""

    alias_module = importlib.import_module(alias)
    target_module = importlib.import_module(target)
    assert alias_module is target_module


def test_public_api_reexports_under_single_package() -> None:
    """Confirm dataclass exports reference the canonical Macros implementations."""

    from macro_system import MacroEngine as package_engine
    from macro_system import MacroOrchestrator as package_orchestrator
    from macro_system.Macros.engine import MacroEngine as macros_engine
    from macro_system.Macros.orchestrator import (
        MacroOrchestrator as macros_orchestrator,
    )

    assert package_engine is macros_engine
    assert package_orchestrator is macros_orchestrator


# === Error & Edge Handling ===
# Alias lookups rely on importlib; failures would surface as ImportError to flag regressions.


# === Performance Considerations ===
# Tests import modules once each; execution cost is negligible relative to suite runtime.


# === Exports / Public API ===
__all__ = ["ALIASES", "test_alias_modules_match_macros_package", "test_public_api_reexports_under_single_package"]
