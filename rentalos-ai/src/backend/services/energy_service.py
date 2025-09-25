"""Energy and sustainability service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import List

from pydantic import BaseModel, Field

from ..plugins.runtime import EnergyTradeContext
from ..utils.energy_utils import carbon_intensity
from ..utils.logger import get_logger
from . import api_service

logger = get_logger(__name__)

_ENERGY_TRADES: List["EnergyTrade"] = []


class EnergyTrade(BaseModel):
    id: int
    asset_id: int
    kilowatt_hours: float
    direction: str
    price_per_kwh: float
    carbon_impact: float
    executed_at: datetime
    recommendations: List[str] = Field(default_factory=list)


def record_energy_trade(
    asset_id: int, kilowatt_hours: float, direction: str, price_per_kwh: float
) -> EnergyTrade:
    carbon = carbon_intensity(kilowatt_hours, kilowatt_hours / 5 if kilowatt_hours else 0)
    context = EnergyTradeContext(
        asset_id=asset_id,
        kilowatt_hours=kilowatt_hours,
        direction=direction,
        market_price=price_per_kwh,
    )
    recommendations: List[str] = []
    adjusted_price = price_per_kwh
    for plugin_name, advice in api_service.collect_energy_recommendations(context):
        adjusted_price += advice.price_adjustment
        carbon += advice.carbon_adjustment
        note = f"{plugin_name}:{advice.label} - {advice.message}"
        recommendations.append(note)
    carbon = max(carbon, 0.0)
    trade = EnergyTrade(
        id=len(_ENERGY_TRADES) + 1,
        asset_id=asset_id,
        kilowatt_hours=kilowatt_hours,
        direction=direction,
        price_per_kwh=round(adjusted_price, 4),
        carbon_impact=round(carbon, 4),
        executed_at=datetime.now(UTC),
        recommendations=recommendations,
    )
    _ENERGY_TRADES.append(trade)
    logger.info("Recorded energy trade", extra={"asset_id": asset_id, "direction": direction})
    return trade


def list_energy_trades() -> List[EnergyTrade]:
    return list(_ENERGY_TRADES)
