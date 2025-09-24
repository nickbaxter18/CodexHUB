import asyncio
import threading

import pytest

from src.agents.orchestrator import Orchestrator
from src.types import TaskList
from src.utils.observer import HealthObserver


class _StubTaskManager:
    def __init__(self) -> None:
        self.restart_event = threading.Event()
        self.restart_calls = 0

    async def create_task(self, coro_factory):  # pragma: no cover - not exercised
        raise NotImplementedError

    async def list_tasks(self) -> TaskList:
        return TaskList(tasks=[])

    async def get_task(self, task_id: str):  # pragma: no cover - not exercised
        return None

    async def wait_for(self, task_id: str):  # pragma: no cover - not exercised
        return None

    def restart(self) -> None:
        self.restart_calls += 1
        self.restart_event.set()


@pytest.mark.asyncio
async def test_health_observer_recovers() -> None:
    observer = HealthObserver(max_failures=1)

    async def async_check() -> dict[str, str]:
        return {"status": "healthy", "detail": "async"}

    observer.register_check("async", async_check)
    observer.record_failure("tasks")

    report = await observer.run_checks()
    assert report.status == "degraded"
    assert any(check.name == "async" for check in report.checks)

    observer.record_success("tasks")
    report = await observer.run_checks()
    assert report.status == "healthy"


@pytest.mark.asyncio
async def test_health_observer_triggers_remediation() -> None:
    observer = HealthObserver(max_failures=1)
    event = asyncio.Event()

    async def failing_check() -> dict[str, str]:
        return {"status": "unhealthy", "detail": "boom"}

    observer.register_check("tasks", failing_check)

    async def remediation() -> None:
        event.set()

    observer.register_remediation("tasks", remediation)

    observer.record_failure("tasks")
    await asyncio.sleep(0)
    await observer.run_checks()

    await asyncio.wait_for(event.wait(), timeout=1)
    assert observer.remediation_history()


@pytest.mark.asyncio
async def test_orchestrator_registers_task_remediation() -> None:
    manager = _StubTaskManager()
    observer = HealthObserver(max_failures=1)
    orchestrator = Orchestrator(manager=manager, observer=observer)

    observer.record_failure("tasks")
    await observer.run_checks()

    assert await asyncio.to_thread(manager.restart_event.wait, 1.0)
    assert manager.restart_calls == 1
    await asyncio.sleep(0)
    assert observer.remediation_history()
    assert observer.failure_counts().get("tasks", 0) == 0
