"""Pricing service implementing deterministic recommendations."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel

from ..orchestrator import dispatcher
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


async def calculate_price(asset_id: int, start_date: datetime, duration: int) -> Dict[str, object]:
    """Generate a pricing recommendation for an asset."""

    base_price = 110 + asset_id * 0.5
    payload = {
        "asset_id": asset_id,
        "base_price": base_price,
        "occupancy": 0.9,
        "sustainability_score": 78,
    }
    logger.info("Calculating price", extra={"asset_id": asset_id})
    agent_result = await dispatcher.dispatch("pricing", payload)
    suggested_price = agent_result["data"]["price"]
    components = [
        PriceComponent(label="base", value=base_price),
        PriceComponent(label="occupancy_adjustment", value=round(suggested_price - base_price, 2)),
    ]
    suggestion = PriceSuggestion(
        asset_id=asset_id,
        start_date=start_date,
        duration=duration,
        suggested_price=suggested_price,
        components=components,
        confidence=agent_result["data"]["confidence"],
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
