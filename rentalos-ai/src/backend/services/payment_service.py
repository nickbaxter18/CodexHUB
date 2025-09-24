"""Payment planning service."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List

from pydantic import BaseModel

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PaymentSchedule(BaseModel):
    due_date: date
    amount: float


class PaymentPlan(BaseModel):
    lease_id: int
    schedules: List[PaymentSchedule]
    split_between: List[str]


async def build_payment_plan(
    lease_id: int, monthly_amount: float, participants: List[str]
) -> PaymentPlan:
    """Create a simple payment plan with rent splitting."""

    start = date.today().replace(day=1)
    schedules = []
    share = round(monthly_amount / max(len(participants), 1), 2)
    for offset in range(3):
        schedules.append(
            PaymentSchedule(due_date=start + timedelta(days=30 * offset), amount=share)
        )
    logger.info("Created payment plan", extra={"lease_id": lease_id})
    return PaymentPlan(lease_id=lease_id, schedules=schedules, split_between=participants)
