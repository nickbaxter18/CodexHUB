import pytest

from src.backend.services.payment_service import build_payment_plan


@pytest.mark.asyncio
async def test_build_payment_plan_split():
    plan = await build_payment_plan(10, 2000.0, ["A", "B"])
    assert plan.lease_id == 10
    assert len(plan.schedules) == 3
    assert all(schedule.amount <= 1000 for schedule in plan.schedules)
