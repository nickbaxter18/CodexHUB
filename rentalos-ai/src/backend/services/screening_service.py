"""Tenant screening service."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel

from ..orchestrator import dispatcher
from ..utils.logger import get_logger
from ..utils.validators import fairness_check

logger = get_logger(__name__)


class ScreeningResult(BaseModel):
    applicant: str
    score: float
    reasons: List[str]
    fairness_flag: bool


async def evaluate_applicant(applicant_data: Dict[str, Any]) -> ScreeningResult:
    """Evaluate an applicant using deterministic rules."""

    payload = {
        "credit_score": applicant_data.get("credit_score", 680),
        "rental_history_years": applicant_data.get("rental_history_years", 3),
    }
    agent_result = await dispatcher.dispatch("screening", payload)
    score = agent_result["data"]["score"]
    reasons = []
    if payload["credit_score"] < 600:
        reasons.append("Low credit score")
    if payload["rental_history_years"] < 2:
        reasons.append("Limited rental history")
    fairness_flag = fairness_check(payload["credit_score"], applicant_data.get("income", 50000))
    return ScreeningResult(
        applicant=applicant_data.get("name", "Unknown"),
        score=score,
        reasons=reasons,
        fairness_flag=fairness_flag,
    )
