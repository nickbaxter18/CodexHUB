"""Scheduling endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..services.scheduling_service import ScheduleEntry, build_schedule

router = APIRouter(tags=["scheduling"])


@router.get("/scheduling/agenda", response_model=List[ScheduleEntry])
async def get_agenda() -> List[ScheduleEntry]:
    items = [
        {"title": "HVAC tune-up", "priority": 2},
        {"title": "Tenant onboarding", "priority": 4},
    ]
    return await build_schedule(items)
