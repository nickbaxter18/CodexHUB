"""Pricing endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from ..services.pricing_service import calculate_price

router = APIRouter(tags=["pricing"])


@router.post("/pricing/suggestions")
async def create_pricing_suggestion(payload: Dict[str, Any]) -> Dict[str, Any]:
    asset_id = int(payload.get("asset_id", 1))
    start_date = datetime.fromisoformat(payload.get("start_date", datetime.utcnow().isoformat()))
    duration = int(payload.get("duration", 7))
    return await calculate_price(asset_id, start_date, duration)
