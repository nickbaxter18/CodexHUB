"""Energy and sustainability service."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel

from ..utils.energy_utils import carbon_intensity
from ..utils.logger import get_logger

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


def record_energy_trade(
    asset_id: int, kilowatt_hours: float, direction: str, price_per_kwh: float
) -> EnergyTrade:
    carbon = carbon_intensity(kilowatt_hours, kilowatt_hours / 5 if kilowatt_hours else 0)
    trade = EnergyTrade(
        id=len(_ENERGY_TRADES) + 1,
        asset_id=asset_id,
        kilowatt_hours=kilowatt_hours,
        direction=direction,
        price_per_kwh=price_per_kwh,
        carbon_impact=carbon,
        executed_at=datetime.utcnow(),
    )
    _ENERGY_TRADES.append(trade)
    logger.info("Recorded energy trade", extra={"asset_id": asset_id, "direction": direction})
    return trade


def list_energy_trades() -> List[EnergyTrade]:
    return list(_ENERGY_TRADES)
