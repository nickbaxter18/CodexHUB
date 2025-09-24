"""Expose orchestrator registry."""

from .agents import (
    AgentRegistry,
    MaintenanceAgent,
    PricingAgent,
    RiskAgent,
    SchedulingAgent,
    ScreeningAgent,
    SustainabilityAgent,
)

registry = AgentRegistry()
registry.register("pricing", PricingAgent())
registry.register("maintenance", MaintenanceAgent())
registry.register("risk", RiskAgent())
registry.register("screening", ScreeningAgent())
registry.register("sustainability", SustainabilityAgent())
registry.register("scheduling", SchedulingAgent())

__all__ = ["registry"]
