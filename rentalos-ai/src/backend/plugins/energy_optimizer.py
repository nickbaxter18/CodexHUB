"""Energy optimisation plugin providing demand-response recommendations."""

from __future__ import annotations

from .runtime import EnergyAdvisorResult, EnergyTradeContext, PluginRuntime

BULK_PURCHASE_THRESHOLD = 15.0
EXPORT_PREMIUM_THRESHOLD = 10.0


def _optimise_trade(context: EnergyTradeContext) -> EnergyAdvisorResult | None:
    """Return dynamic pricing and carbon adjustments for a trade."""

    price_adjustment = 0.0
    carbon_adjustment = 0.0
    notes: list[str] = []

    if context.direction.lower() == "buy":
        carbon_adjustment -= context.kilowatt_hours * 0.03
        notes.append("offset demand with community solar credits")
        if context.kilowatt_hours >= BULK_PURCHASE_THRESHOLD:
            price_adjustment -= 0.01
            notes.append("applied bulk purchase incentive")
    elif context.direction.lower() == "sell":
        carbon_adjustment -= context.kilowatt_hours * 0.05
        notes.append("registered renewable energy certificates")
        if context.kilowatt_hours >= EXPORT_PREMIUM_THRESHOLD:
            price_adjustment += 0.012
            notes.append("added premium for high-capacity export")

    if not notes:
        return None

    return EnergyAdvisorResult(
        label="demand_response",
        message="; ".join(notes),
        price_adjustment=round(price_adjustment, 4),
        carbon_adjustment=round(carbon_adjustment, 4),
    )


def setup_plugin(runtime: PluginRuntime) -> None:
    """Register the optimisation logic with the runtime."""

    runtime.register_energy_advisor(_optimise_trade)
