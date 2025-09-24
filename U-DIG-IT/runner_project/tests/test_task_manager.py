import pytest

from src.execution.task_manager import TaskManager
from src.types import TaskStatus


@pytest.mark.asyncio
async def test_task_manager_success():
    manager = TaskManager()

    async def job():
        return {"result": "ok"}

    creation = await manager.create_task(job)
    task = await manager.wait_for(creation.task_id)
    assert task is not None
    assert task.status == TaskStatus.COMPLETED
    assert task.result == {"result": "ok"}


@pytest.mark.asyncio
async def test_task_manager_failure():
    manager = TaskManager()

    async def job():
        raise RuntimeError("boom")

    creation = await manager.create_task(job)
    task = await manager.wait_for(creation.task_id)
    assert task is not None
    assert task.status == TaskStatus.FAILED
    assert task.error == "boom"
