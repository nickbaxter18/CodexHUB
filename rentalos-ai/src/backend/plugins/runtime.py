"""Plugin runtime dataclasses and registration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass(frozen=True)
class PricingContext:
    """Context describing the current pricing computation."""

    asset_id: int
    base_price: float
    occupancy: float
    esg_score: float
    duration: int


@dataclass(frozen=True)
class PricingAdjustment:
    """Represents a pricing delta contributed by a plugin."""

    label: str
    amount: float
    rationale: Optional[str] = None


@dataclass(frozen=True)
class EnergyTradeContext:
    """Context for optimisation of an energy trade."""

    asset_id: int
    kilowatt_hours: float
    direction: str
    market_price: float


@dataclass(frozen=True)
class EnergyAdvisorResult:
    """Actionable recommendation emitted by an energy plugin."""

    label: str
    message: str
    price_adjustment: float = 0.0
    carbon_adjustment: float = 0.0


PricingAdjuster = Callable[[PricingContext], Optional[PricingAdjustment]]
EnergyAdvisor = Callable[[EnergyTradeContext], Optional[EnergyAdvisorResult]]


class PluginRuntime:
    """Mutable registry of callbacks exposed to plugin entrypoints."""

    def __init__(self, plugin_name: str) -> None:
        self.plugin_name = plugin_name
        self.pricing_adjusters: List[PricingAdjuster] = []
        self.energy_advisors: List[EnergyAdvisor] = []

    def register_pricing_adjuster(self, adjuster: PricingAdjuster) -> None:
        """Register a callback that returns an optional pricing adjustment."""

        self.pricing_adjusters.append(adjuster)

    def register_energy_advisor(self, advisor: EnergyAdvisor) -> None:
        """Register a callback that augments energy trades."""

        self.energy_advisors.append(advisor)
