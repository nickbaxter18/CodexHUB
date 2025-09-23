"""Header & Purpose: macro system package entry point with Macros aliases."""

from __future__ import annotations

# === Imports / Dependencies ===
import importlib
import sys
from types import ModuleType
from typing import Dict, Mapping

from .Macros import (
    AgentAssignment,
    DEFAULT_AGENT_MAP,
    Macro,
    MacroAudit,
    MacroCycleError,
    MacroDefinitionError,
    MacroEngine,
    MacroError,
    MacroNotFoundError,
    MacroOrchestrator,
    MacroPlanner,
    MacroRenderError,
    MacroRepository,
    MacroStats,
    MacroValidationError,
    PlanStep,
)

# === Types / Interfaces / Schemas ===
AliasMap = Mapping[str, str]
AliasRegistry = Dict[str, ModuleType]


# === Core Logic / Implementation ===
def _register_alias_modules(alias_map: AliasMap) -> AliasRegistry:
    """Import Macros submodules and register legacy alias modules."""

    registered: AliasRegistry = {}
    for alias, target in alias_map.items():
        full_name = f"{__name__}.{alias}"
        try:
            module = importlib.import_module(target)
        except ImportError as exc:  # pragma: no cover - defensive guard
            raise RuntimeError(
                f"Failed to import legacy macro module alias '{target}'."
            ) from exc
        sys.modules.setdefault(full_name, module)
        registered[alias] = module
    return registered


_ALIAS_MODULES: AliasMap = {
    "cli": "macro_system.Macros.cli",
    "engine": "macro_system.Macros.engine",
    "macros": "macro_system.Macros.catalog",
    "repository": "macro_system.Macros.repository",
    "planner": "macro_system.Macros.planner",
    "orchestrator": "macro_system.Macros.orchestrator",
    "types": "macro_system.Macros.types",
}

_ALIASED_MODULES: AliasRegistry = _register_alias_modules(_ALIAS_MODULES)


def __getattr__(name: str) -> ModuleType:
    """Expose registered alias modules via attribute access."""

    if name in _ALIASED_MODULES:
        return _ALIASED_MODULES[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Display dataclass exports alongside registered aliases."""

    return sorted(set(__all__) | set(_ALIASED_MODULES))


# === Error & Edge Handling ===
# ``_register_alias_modules`` raises ``RuntimeError`` with context if imports fail.
# ``__getattr__`` surfaces ``AttributeError`` for unknown names, aligning with Python expectations.


# === Performance Considerations ===
# Alias registration imports each Macros module once and caches them in ``sys.modules``.


# === Exports / Public API ===
__all__ = [
    "AgentAssignment",
    "DEFAULT_AGENT_MAP",
    "Macro",
    "MacroAudit",
    "MacroCycleError",
    "MacroDefinitionError",
    "MacroEngine",
    "MacroError",
    "MacroNotFoundError",
    "MacroOrchestrator",
    "MacroPlanner",
    "MacroRenderError",
    "MacroRepository",
    "MacroStats",
    "MacroValidationError",
    "PlanStep",
]
