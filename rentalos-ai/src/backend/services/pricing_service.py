"""Pricing service implementing data-informed recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import pstdev
from typing import Dict, Iterable, List

from pydantic import BaseModel

from ..orchestrator import dispatcher
from ..orchestrator.knowledge_base import knowledge_base
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PriceComponent(BaseModel):
    label: str
    value: float


class PriceSuggestion(BaseModel):
    asset_id: int
    start_date: datetime
    duration: int
    suggested_price: float
    components: List[PriceComponent]
    confidence: float


@dataclass
class MarketSnapshot:
    """Represents recent demand signals for an asset."""

    occupancy: float
    demand_index: float
    competitor_rate: float


def ingest_market_snapshot(
    asset_id: int, rate: float, occupancy: float, esg_score: float, demand_index: float
) -> None:
    """Persist signals to the knowledge base so pricing remains contextual."""

    entity = f"asset:{asset_id}"
    knowledge_base.record_metric(entity, "rate", rate)
    knowledge_base.record_metric(entity, "occupancy", occupancy)
    knowledge_base.record_metric(entity, "esg", esg_score)
    knowledge_base.record_metric(entity, "demand", demand_index)


def _weighted_average(values: Iterable[float]) -> float:
    window = list(values)
    if not window:
        raise ValueError("values cannot be empty")
    weights = list(range(1, len(window) + 1))
    total_weight = sum(weights)
    weighted_sum = sum(value * weight for value, weight in zip(window, weights, strict=False))
    return weighted_sum / total_weight


def _forecast_base_rate(asset_id: int) -> float:
    series = knowledge_base.get_metric_series(f"asset:{asset_id}", "rate", limit=8)
    if series:
        try:
            return _weighted_average(series)
        except ValueError:
            pass
    return 110 + asset_id * 0.5


def _latest_snapshot(asset_id: int) -> MarketSnapshot:
    entity = f"asset:{asset_id}"
    occupancy = knowledge_base.latest_metric(entity, "occupancy") or 0.9
    competitor = knowledge_base.latest_metric(entity, "rate") or (
        _forecast_base_rate(asset_id) * 1.05
    )
    demand_index = knowledge_base.latest_metric(entity, "demand") or 1.0
    return MarketSnapshot(
        occupancy=float(occupancy),
        demand_index=float(demand_index),
        competitor_rate=float(competitor),
    )


def _confidence_from_history(asset_id: int) -> float:
    series = knowledge_base.get_metric_series(f"asset:{asset_id}", "rate", limit=8)
    if len(series) < 2:
        return 0.7
    variability = pstdev(series)
    # Higher variability reduces the confidence interval.
    return max(0.55, 0.9 - min(variability / 100, 0.3))


async def calculate_price(asset_id: int, start_date: datetime, duration: int) -> Dict[str, object]:
    """Generate a pricing recommendation for an asset.

    The routine analyses recent market signals from the knowledge base and
    adjusts the deterministic Stage 1 model with demand and sustainability
    context. This keeps the runtime light while reflecting data driven
    behaviour expected from Stage 2.
    """

    base_price = _forecast_base_rate(asset_id)
    snapshot = _latest_snapshot(asset_id)
    esg_score = knowledge_base.latest_metric(f"asset:{asset_id}", "esg") or 75.0
    sustainability_modifier = 1 + (esg_score - 70) / 500
    demand_modifier = 1 + (snapshot.demand_index - 1.0) / 4
    occupancy_modifier = 1 + (snapshot.occupancy - 0.85) / 5

    adjusted_base = base_price * sustainability_modifier * demand_modifier * occupancy_modifier
    payload = {
        "asset_id": asset_id,
        "base_price": adjusted_base,
        "occupancy": snapshot.occupancy,
        "sustainability_score": esg_score,
    }
    logger.info("Calculating price", extra={"asset_id": asset_id})
    agent_result = await dispatcher.dispatch("pricing", payload)
    suggested_price = agent_result["data"]["price"]
    occupancy_component = round(adjusted_base - base_price, 2)
    agent_component = round(suggested_price - adjusted_base, 2)
    components = [
        PriceComponent(label="base", value=round(base_price, 2)),
        PriceComponent(label="market_adjustment", value=occupancy_component),
        PriceComponent(label="agent_adjustment", value=agent_component),
    ]
    suggestion = PriceSuggestion(
        asset_id=asset_id,
        start_date=start_date,
        duration=duration,
        suggested_price=round(suggested_price, 2),
        components=components,
        confidence=_confidence_from_history(asset_id),
    )
    return suggestion.model_dump()


def get_pricing_history(asset_id: int) -> List[Dict[str, float]]:
    """Return synthetic pricing history for the asset."""

    history = []
    base = 100 + asset_id
    for week in range(4):
        history.append({"week": week, "price": round(base + week * 1.5, 2)})
    return history


def update_pricing_rules(rules: Dict[str, float]) -> Dict[str, float]:
    """Echo the provided rules to simulate persistence."""

    logger.debug("Updating pricing rules", extra={"rules": rules})
    return rules
