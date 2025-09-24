import pytest

from src.backend.services.maintenance_service import generate_schedule


@pytest.mark.asyncio
async def test_generate_schedule_creates_tasks():
    tasks = await generate_schedule(1)
    assert len(tasks) == 2
    assert tasks[0].asset_id == 1
