"""Energy endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..services.energy_service import EnergyTrade, record_energy_trade

router = APIRouter(tags=["energy"])


@router.post("/energy/trade", response_model=EnergyTrade)
def record_trade(payload: Dict[str, Any]) -> EnergyTrade:
    asset_id = int(payload.get("asset_id", 1))
    kwh = float(payload.get("kilowatt_hours", 12.5))
    direction = str(payload.get("direction", "sell"))
    price = float(payload.get("price_per_kwh", 0.15))
    return record_energy_trade(asset_id, kwh, direction, price)
