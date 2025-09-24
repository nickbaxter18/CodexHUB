"""Predictive maintenance service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel, Field

from ..orchestrator import dispatcher
from ..utils.logger import get_logger
from ..utils.scheduling import add_minutes

logger = get_logger(__name__)


class MaintenanceTask(BaseModel):
    asset_id: int
    scheduled_for: datetime
    description: str
    severity: str = Field(pattern="^(low|medium|high)$")


async def generate_schedule(asset_id: int) -> List[MaintenanceTask]:
    """Generate maintenance tasks using deterministic heuristics."""

    now = datetime.utcnow()
    payload = {
        "asset_id": asset_id,
        "sensor_alerts": 3,
        "tasks": ["inspect HVAC", "check sensors"],
    }
    agent_result = await dispatcher.dispatch("maintenance", payload)
    severity = agent_result["data"]["severity"]
    tasks = [
        MaintenanceTask(
            asset_id=asset_id,
            scheduled_for=add_minutes(now, 60),
            description="inspect HVAC",
            severity=severity,
        ),
        MaintenanceTask(
            asset_id=asset_id,
            scheduled_for=add_minutes(now, 180),
            description="check sensors",
            severity="low",
        ),
    ]
    logger.info(
        "Generated maintenance schedule", extra={"asset_id": asset_id, "severity": severity}
    )
    return tasks


def get_maintenance_history(asset_id: int) -> List[str]:
    """Provide maintenance history entries."""

    return [f"Asset {asset_id} inspection completed", "Filters replaced"]


def schedule_drone_inspection(asset_id: int) -> MaintenanceTask:
    """Schedule a drone inspection for the asset."""

    return MaintenanceTask(
        asset_id=asset_id,
        scheduled_for=datetime.utcnow() + timedelta(days=2),
        description="Drone roof scan",
        severity="medium",
    )
