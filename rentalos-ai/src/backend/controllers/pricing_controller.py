"""Pricing endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..services.pricing_service import calculate_price

router = APIRouter(tags=["pricing"])


def _resolve_start_date(raw_value: str | None) -> datetime:
    """Parse the provided ISO timestamp and normalise it to UTC."""

    if not raw_value:
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError as exc:  # pragma: no cover - validation
        raise HTTPException(status_code=400, detail="Invalid start_date format") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


@router.post("/pricing/suggestions")
async def create_pricing_suggestion(payload: Dict[str, Any]) -> Dict[str, Any]:
    asset_id = int(payload.get("asset_id", 1))
    start_date = _resolve_start_date(payload.get("start_date"))
    duration = int(payload.get("duration", 7))
    return await calculate_price(asset_id, start_date, duration)
