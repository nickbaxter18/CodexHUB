import pytest

from src.backend.services.scheduling_service import build_schedule


@pytest.mark.asyncio
async def test_build_schedule_orders_by_priority():
    items = [
        {"title": "B Task", "priority": 3},
        {"title": "A Task", "priority": 1},
    ]
    schedule = await build_schedule(items)
    assert schedule[0].title == "A Task"
