"""Primary exports for the Macros package."""

"""Header & Purpose: surface primary Macros package exports."""

# === Imports / Dependencies ===
from .catalog import load_catalogs, load_default_catalog, load_macros
from .engine import MacroEngine
from .orchestrator import DEFAULT_AGENT_MAP, MacroOrchestrator
from .planner import MacroPlanner
from .repository import MacroRepository
from .types import (
    AgentAssignment,
    Macro,
    MacroAudit,
    MacroCycleError,
    MacroDefinitionError,
    MacroError,
    MacroNotFoundError,
    MacroRenderError,
    MacroStats,
    MacroValidationError,
    PlanStep,
)

# === Types / Interfaces / Schemas ===
# Exports include dataclasses, exceptions, and loader utilities.


# === Core Logic / Implementation ===
# Centralises exports to simplify consumers' import paths.


# === Error & Edge Handling ===
# Errors are defined within ``types`` and re-exported for package users.


# === Performance Considerations ===
# Central re-export adds no overhead; actual logic resides in submodules.


# === Exports / Public API ===
__all__ = [
    "AgentAssignment",
    "Macro",
    "MacroAudit",
    "MacroCycleError",
    "MacroDefinitionError",
    "MacroEngine",
    "MacroError",
    "MacroNotFoundError",
    "MacroPlanner",
    "MacroOrchestrator",
    "MacroRenderError",
    "MacroStats",
    "MacroValidationError",
    "PlanStep",
    "MacroRepository",
    "DEFAULT_AGENT_MAP",
    "load_catalogs",
    "load_default_catalog",
    "load_macros",
]
