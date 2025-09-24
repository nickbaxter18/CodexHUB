"""ESG reporting service."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel

from ..orchestrator import dispatcher
from ..utils.energy_utils import carbon_intensity
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ESGMetric(BaseModel):
    name: str
    value: float
    unit: str


class ESGReport(BaseModel):
    asset_id: int
    score: float
    metrics: List[ESGMetric]


async def compile_esg_report(asset_id: int, indicators: Dict[str, float]) -> ESGReport:
    """Compile ESG metrics and score."""

    payload = {
        "carbon_kg": indicators.get("carbon_kg", 120),
        "water_liters": indicators.get("water_liters", 900),
        "waste_kg": indicators.get("waste_kg", 40),
    }
    agent_result = await dispatcher.dispatch("sustainability", payload)
    metrics = [
        ESGMetric(name="carbon", value=payload["carbon_kg"], unit="kg"),
        ESGMetric(name="water", value=payload["water_liters"], unit="liters"),
        ESGMetric(name="waste", value=payload["waste_kg"], unit="kg"),
        ESGMetric(
            name="carbon_intensity", value=carbon_intensity(payload["carbon_kg"], 45), unit="kg/kWh"
        ),
    ]
    return ESGReport(asset_id=asset_id, score=agent_result["data"]["esg_score"], metrics=metrics)
