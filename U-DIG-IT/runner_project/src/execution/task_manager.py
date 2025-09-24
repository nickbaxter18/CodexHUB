"""Task manager for the runner."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, Optional
from uuid import uuid4

from ..errors import TaskError
from ..types import Task, TaskCreation, TaskList, TaskStatus
from ..utils.logger import get_logger

LOGGER = get_logger("task_manager")


class TaskManager:
    """Manage asynchronous tasks and their results."""

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    async def create_task(
        self, coro_factory: Callable[[], Coroutine[Any, Any, Any]]
    ) -> TaskCreation:
        """Create and schedule a new task."""

        task_id = uuid4().hex
        now = datetime.now(timezone.utc)
        with self._lock:
            self._tasks[task_id] = Task(
                id=task_id,
                status=TaskStatus.PENDING,
                created_at=now,
                updated_at=now,
                result=None,
                error=None,
            )

        loop = asyncio.get_running_loop()

        def execute() -> None:
            self._set_status(task_id, TaskStatus.RUNNING)
            try:
                result = asyncio.run(coro_factory())
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Task %s failed", task_id)
                self._set_failure(task_id, exc)
            else:
                self._set_result(task_id, result)

        loop.run_in_executor(None, execute)
        return TaskCreation(task_id=task_id, status=TaskStatus.PENDING)

    def _set_status(self, task_id: str, status: TaskStatus) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskError(f"Task {task_id} not found")
            task.status = status
            task.updated_at = datetime.now(timezone.utc)

    def _set_result(self, task_id: str, result: Any) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskError(f"Task {task_id} not found")
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.error = None
            task.updated_at = datetime.now(timezone.utc)

    def _set_failure(self, task_id: str, exc: Exception) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskError(f"Task {task_id} not found")
            task.status = TaskStatus.FAILED
            task.result = None
            task.error = str(exc)
            task.updated_at = datetime.now(timezone.utc)

    async def get_task(self, task_id: str) -> Optional[Task]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return Task(
                id=task.id,
                status=task.status,
                created_at=task.created_at,
                updated_at=task.updated_at,
                result=task.result,
                error=task.error,
            )

    async def list_tasks(self) -> TaskList:
        with self._lock:
            tasks = [
                Task(
                    id=task.id,
                    status=task.status,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    result=task.result,
                    error=task.error,
                )
                for task in self._tasks.values()
            ]
        return TaskList(tasks=tasks)

    async def wait_for(self, task_id: str) -> Optional[Task]:
        """Wait until the task reaches a terminal state."""

        while True:
            task = await self.get_task(task_id)
            if task is None:
                return None
            if task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
                return task
            await asyncio.sleep(0.05)


DEFAULT_TASK_MANAGER = TaskManager()
