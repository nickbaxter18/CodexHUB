"""Maintenance endpoints."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter

from ..services.maintenance_service import MaintenanceTask, generate_schedule

router = APIRouter(tags=["maintenance"])


@router.post("/maintenance/schedule", response_model=List[MaintenanceTask])
async def create_schedule(payload: Dict[str, int]) -> List[MaintenanceTask]:
    asset_id = int(payload.get("asset_id", 1))
    return await generate_schedule(asset_id)
