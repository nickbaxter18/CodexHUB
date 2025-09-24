"""Agent definitions used for orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class AgentResult:
    name: str
    data: Dict[str, Any]
    generated_at: datetime


class BaseAgent:
    """Base class for orchestrated agents."""

    name: str = "agent"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError


class PricingAgent(BaseAgent):
    name = "pricing"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        base_price = float(payload.get("base_price", 120.0))
        occupancy = float(payload.get("occupancy", 0.92))
        sustainability = float(payload.get("sustainability_score", 75))
        adjustment = (1 + occupancy / 10) - (100 - sustainability) / 200
        price = base_price * adjustment
        return AgentResult(
            self.name, {"price": round(price, 2), "confidence": 0.82}, datetime.utcnow()
        )


class MaintenanceAgent(BaseAgent):
    name = "maintenance"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        severity = "medium"
        if payload.get("sensor_alerts", 0) > 5:
            severity = "high"
        return AgentResult(
            self.name, {"severity": severity, "tasks": payload.get("tasks", [])}, datetime.utcnow()
        )


class RiskAgent(BaseAgent):
    name = "risk"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        score = max(0.0, min(1.0, 0.5 + payload.get("esg_score", 0) / 200))
        return AgentResult(self.name, {"risk_score": score}, datetime.utcnow())


class ScreeningAgent(BaseAgent):
    name = "screening"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        credit = payload.get("credit_score", 680)
        history = payload.get("rental_history_years", 3)
        score = min(100, credit / 10 + history * 5)
        return AgentResult(self.name, {"score": score}, datetime.utcnow())


class SustainabilityAgent(BaseAgent):
    name = "sustainability"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        carbon = payload.get("carbon_kg", 120)
        water = payload.get("water_liters", 800)
        waste = payload.get("waste_kg", 32)
        composite = max(0, 100 - (carbon / 10 + water / 50 + waste))
        return AgentResult(self.name, {"esg_score": round(composite, 2)}, datetime.utcnow())


class SchedulingAgent(BaseAgent):
    name = "scheduling"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        items = payload.get("items", [])
        ordered = sorted(items, key=lambda item: item.get("priority", 5))
        return AgentResult(self.name, {"ordered": ordered}, datetime.utcnow())


class AgentRegistry:
    """Registry that maps agent names to instances."""

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        self._agents[name] = agent

    def get(self, name: str) -> BaseAgent:
        if name not in self._agents:
            raise KeyError(f"Agent {name} is not registered")
        return self._agents[name]
