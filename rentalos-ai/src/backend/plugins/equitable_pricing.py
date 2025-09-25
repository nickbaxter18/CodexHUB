"""Fairness-focused pricing plugin."""

from __future__ import annotations

from statistics import fmean

from .runtime import PluginRuntime, PricingAdjustment, PricingContext


def _compute_affordability_adjustment(context: PricingContext) -> PricingAdjustment | None:
    """Return a fairness discount when occupancy spikes or ESG scores excel."""

    modifiers: list[str] = []
    adjustment = 0.0

    if context.occupancy >= 0.95:
        adjustment -= min(context.base_price * 0.04, 30.0)
        modifiers.append("capping rent under peak occupancy")

    if context.esg_score >= 85:
        adjustment -= 5.0
        modifiers.append("rewarding sustainability leadership")
    elif context.esg_score < 60:
        adjustment += min(context.base_price * 0.02, 18.0)
        modifiers.append("funding ESG remediation")

    if not modifiers:
        return None

    return PricingAdjustment(
        label="fairness_adjustment",
        amount=round(adjustment, 2),
        rationale="; ".join(modifiers),
    )


def _stability_buffer(context: PricingContext) -> PricingAdjustment | None:
    """Encourage pricing stability over longer durations."""

    if context.duration < 14:
        return None

    window = [context.base_price * multiplier for multiplier in (0.98, 1.0, 1.02, 1.01)]
    averaged = fmean(window)
    delta = averaged - context.base_price
    if abs(delta) < 1:
        return None
    rationale = "promoting rate stability for extended stays"
    return PricingAdjustment(label="stability_buffer", amount=round(delta, 2), rationale=rationale)


def setup_plugin(runtime: PluginRuntime) -> None:
    """Register pricing adjusters for the fairness plugin."""

    runtime.register_pricing_adjuster(_compute_affordability_adjustment)
    runtime.register_pricing_adjuster(_stability_buffer)
