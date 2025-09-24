"""Predictive maintenance service with anomaly detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import fmean, pstdev
from typing import Dict, List, Sequence

from pydantic import BaseModel, Field

from ..orchestrator import dispatcher
from ..orchestrator.knowledge_base import knowledge_base
from ..utils.logger import get_logger
from ..utils.scheduling import add_minutes

logger = get_logger(__name__)


class MaintenanceTask(BaseModel):
    asset_id: int
    scheduled_for: datetime
    description: str
    severity: str = Field(pattern="^(low|medium|high)$")


class SensorWindow(BaseModel):
    """Represents a short aggregation of sensor samples."""

    metric: str
    samples: List[float]

    def average(self) -> float:
        return fmean(self.samples) if self.samples else 0.0

    def stdev(self) -> float:
        return pstdev(self.samples) if len(self.samples) > 1 else 0.0


def detect_anomalies(windows: Sequence[SensorWindow], threshold: float = 1.5) -> Dict[str, float]:
    """Return a mapping of metric -> anomaly score."""

    scores: Dict[str, float] = {}
    for window in windows:
        baseline = knowledge_base.get_metric_series("sensor:" + window.metric, "avg", limit=12)
        baseline_mean = fmean(baseline) if baseline else window.average()
        if len(baseline) > 1:
            baseline_stdev = pstdev(baseline)
        elif baseline:
            baseline_stdev = 0.1
        else:
            baseline_stdev = window.stdev() or 0.1
        deviation = abs(window.average() - baseline_mean)
        severity_ratio = window.stdev() / (baseline_stdev or 0.1)
        score = max(deviation / baseline_stdev if baseline_stdev else 0.0, severity_ratio)
        if score >= threshold:
            scores[window.metric] = round(score, 2)
        knowledge_base.record_metric("sensor:" + window.metric, "avg", window.average())
    return scores


async def generate_schedule(
    asset_id: int, sensor_windows: Sequence[SensorWindow] | None = None
) -> List[MaintenanceTask]:
    """Generate maintenance tasks using deterministic heuristics plus anomalies."""

    sensor_windows = sensor_windows or []
    anomaly_scores = detect_anomalies(sensor_windows)
    now = datetime.now(UTC)
    severity = "medium" if anomaly_scores else "low"
    payload = {
        "asset_id": asset_id,
        "sensor_alerts": len(anomaly_scores),
        "tasks": ["inspect HVAC", "check sensors"],
    }
    agent_result = await dispatcher.dispatch("maintenance", payload)
    severity = max(severity, agent_result["data"]["severity"], key=["low", "medium", "high"].index)
    base_tasks = [
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

    for metric, score in anomaly_scores.items():
        base_tasks.append(
            MaintenanceTask(
                asset_id=asset_id,
                scheduled_for=add_minutes(now, 30),
                description=f"Investigate anomaly in {metric}",
                severity="high" if score > 4 else "medium",
            )
        )

    logger.info(
        "Generated maintenance schedule",
        extra={"asset_id": asset_id, "anomalies": anomaly_scores},
    )
    return base_tasks


def get_maintenance_history(asset_id: int) -> List[str]:
    """Provide maintenance history entries."""

    return [f"Asset {asset_id} inspection completed", "Filters replaced"]


def schedule_drone_inspection(asset_id: int) -> MaintenanceTask:
    """Schedule a drone inspection for the asset."""

    return MaintenanceTask(
        asset_id=asset_id,
        scheduled_for=datetime.now(UTC) + timedelta(days=2),
        description="Drone roof scan",
        severity="medium",
    )
