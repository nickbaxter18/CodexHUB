import asyncio

import pytest

from src.execution.task_manager import TaskManager
from src.types import Task, TaskStatus


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


@pytest.mark.asyncio
async def test_task_manager_auto_retry() -> None:
    attempts = 0
    manager = TaskManager(max_retries=1)

    async def job():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient failure")
        return {"result": "ok"}

    creation = await manager.create_task(job)
    task = await manager.wait_for(creation.task_id)

    assert attempts == 2
    assert task is not None
    assert task.status == TaskStatus.COMPLETED
    assert task.result == {"result": "ok"}
    assert task.error is None


@pytest.mark.asyncio
async def test_task_manager_restart_recovers_event_loop() -> None:
    manager = TaskManager()

    await asyncio.to_thread(manager.restart)

    async def job() -> str:
        return "ok"

    creation = await manager.create_task(job)
    task = await manager.wait_for(creation.task_id)

    assert task is not None
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "ok"
    assert task.error is None


def test_task_manager_survives_event_loop_shutdown() -> None:
    manager = TaskManager()

    async def job() -> str:
        await asyncio.sleep(0)
        return "ok"

    async def schedule() -> str:
        creation = await manager.create_task(job)
        return creation.task_id

    task_id = asyncio.run(schedule())

    async def await_result() -> Task:
        task = await manager.wait_for(task_id)
        assert task is not None
        return task

    task = asyncio.run(await_result())

    assert task.status == TaskStatus.COMPLETED
    assert task.result == "ok"
