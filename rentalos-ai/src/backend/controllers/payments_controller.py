"""Payments endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..services.payment_service import PaymentPlan, build_payment_plan

router = APIRouter(tags=["payments"])


@router.post("/payments/plan", response_model=PaymentPlan)
async def create_payment_plan(payload: Dict[str, Any]) -> PaymentPlan:
    lease_id = int(payload.get("lease_id", 1))
    monthly_amount = float(payload.get("monthly_amount", 1800))
    participants = list(payload.get("participants", ["Tenant A"]))
    return await build_payment_plan(lease_id, monthly_amount, participants)
