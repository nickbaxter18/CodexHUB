"""Ethics agent applying fairness heuristics."""

from __future__ import annotations

from typing import Any, Dict, List

from ..config import get_config
from ..errors import EthicsError
from .base import Agent


class EthicsAgent(Agent):
    """Compute fairness scores and approve or reject actions."""

    def __init__(self) -> None:
        super().__init__(name="ethics")
        self._config = get_config()
        self._history: List[float] = []
        self._dynamic_threshold = self._config.fairness_threshold

    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        feedback = context.get("fairness")
        if isinstance(feedback, (int, float)):
            self._history.append(float(feedback))
            self._history = self._history[-100:]
            self._dynamic_threshold = max(
                0.0,
                min(
                    1.0,
                    self._config.fairness_threshold
                    + self._config.fairness_dynamic_margin * (1.0 - float(feedback)),
                ),
            )
        return context

    async def act(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        risk_score = float(payload.get("risk", 0.0))
        mitigations = payload.get("mitigations") or []
        mitigation_bonus = 0.05 * len(mitigations)
        fairness = max(0.0, min(1.0, 1.0 - risk_score + mitigation_bonus))
        sensitivity = float(payload.get("sensitivity", 1.0))
        threshold = max(0.0, min(1.0, self._dynamic_threshold * sensitivity))
        approved = fairness >= threshold or bool(payload.get("override"))
        if not approved and payload.get("strict", False):
            raise EthicsError("Action rejected due to fairness threshold breach")
        self._history.append(fairness)
        self._history = self._history[-100:]
        self._dynamic_threshold = threshold
        return {
            "approved": approved,
            "fairness": fairness,
            "threshold": self._config.fairness_threshold,
            "dynamic_threshold": threshold,
            "history": self._history[-5:],
        }

    def stats(self) -> Dict[str, Any]:
        """Expose fairness metrics for dashboards."""

        return {
            "fairness_threshold": self._config.fairness_threshold,
            "dynamic_threshold": self._dynamic_threshold,
            "history": list(self._history[-10:]),
        }
