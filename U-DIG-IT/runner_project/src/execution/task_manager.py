"""Task manager for the runner."""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import Future
from contextlib import suppress
from contextvars import copy_context
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, Optional
from uuid import uuid4

from ..errors import RunnerError, TaskError
from ..types import Task, TaskCreation, TaskList, TaskStatus
from ..utils.logger import get_logger

LOGGER = get_logger("task_manager")


def _default_retry_budget() -> int:
    """Derive the retry budget from configuration when available."""

    try:
        from ..config import get_config
    except Exception:  # pragma: no cover - configuration import failure
        return 0
    try:
        config = get_config()
    except Exception:  # pragma: no cover - configuration resolution failure
        return 0
    return max(0, int(config.max_task_failures) - 1)


class TaskManager:
    """Manage asynchronous tasks, supporting optional automatic retries."""

    def __init__(self, max_retries: Optional[int] = None) -> None:
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._loop_lock = threading.Lock()
        if max_retries is None:
            retry_budget = _default_retry_budget()
        else:
            retry_budget = max(0, max_retries)
        self._max_retries = retry_budget
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._start_loop()

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

        context = copy_context()

        async def runner() -> None:
            attempt = 0
            while True:
                self._set_status(task_id, TaskStatus.RUNNING)
                try:
                    result = await context.run(coro_factory)
                except asyncio.CancelledError:  # pragma: no cover - currently unused
                    self._set_failure(task_id, TaskError("Task was cancelled"))
                    return
                except Exception as exc:  # noqa: BLE001
                    should_retry = attempt < self._max_retries and not isinstance(exc, RunnerError)
                    if should_retry:
                        LOGGER.warning(
                            "Task %s failed on attempt %s/%s: %s",
                            task_id,
                            attempt + 1,
                            self._max_retries + 1,
                            exc,
                        )
                        self._set_status(task_id, TaskStatus.PENDING)
                        attempt += 1
                        await asyncio.sleep(0)
                        continue
                    if isinstance(exc, RunnerError):
                        LOGGER.warning("Task %s failed: %s", task_id, exc)
                    else:
                        LOGGER.exception("Task %s failed on final attempt", task_id)
                    self._set_failure(task_id, exc)
                    return
                else:
                    self._set_result(task_id, result)
                    return

        def _log_future(fut: Future) -> None:  # pragma: no cover - defensive logging
            exc = fut.exception()
            if exc is not None:
                LOGGER.exception("Task runner failed", exc_info=exc)

        with self._loop_lock:
            loop = self._loop
        if loop is None:
            raise TaskError("Task manager event loop is not running")
        try:
            future = asyncio.run_coroutine_threadsafe(runner(), loop)
        except RuntimeError as exc:  # pragma: no cover - defensive guard
            raise TaskError("Task manager event loop is not running") from exc
        future.add_done_callback(_log_future)
        return TaskCreation(task_id=task_id, status=TaskStatus.PENDING)

    @staticmethod
    def _run_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            with suppress(Exception):
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    def _start_loop(self) -> None:
        loop = asyncio.new_event_loop()
        thread = threading.Thread(
            target=self._run_loop,
            args=(loop,),
            name="task-manager-loop",
            daemon=True,
        )
        thread.start()
        with self._loop_lock:
            self._loop = loop
            self._thread = thread

    def _stop_loop(self) -> None:
        with self._loop_lock:
            loop = self._loop
            thread = self._thread
            self._loop = None
            self._thread = None
        if loop is None or thread is None:
            return
        if loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=2.0)

    def restart(self) -> None:
        """Restart the background event loop used to execute tasks."""

        LOGGER.warning("Restarting task manager event loop after remediation")
        self._stop_loop()
        self._start_loop()

    def shutdown(self) -> None:
        """Stop the background event loop."""

        self._stop_loop()

    @property
    def max_retries(self) -> int:
        return self._max_retries

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
