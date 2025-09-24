"""Health and resilience utilities for Stage 3."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Awaitable, Callable, Deque, Dict, List, Union

from ..types import HealthCheck, HealthReport
from .logger import get_logger

LOGGER = get_logger("observer")

CheckResult = Union[bool, HealthCheck, Dict[str, str]]
CheckCallable = Callable[[], Union[CheckResult, Awaitable[CheckResult]]]
RemediationCallable = Callable[[], Union[None, Awaitable[None]]]


class HealthObserver:
    """Track health checks and repeated failures for auto-healing."""

    def __init__(self, max_failures: int = 3) -> None:
        self._checks: Dict[str, CheckCallable] = {}
        self._failures: Dict[str, int] = {}
        self._recent_failures: Deque[str] = deque(maxlen=20)
        self._remediations: Dict[str, RemediationCallable] = {}
        self._remediation_state: Dict[str, str] = {}
        self._pending_remediation: set[str] = set()
        self._recent_remediations: Deque[str] = deque(maxlen=20)
        self.max_failures = max_failures

    def register_check(self, name: str, func: CheckCallable) -> None:
        self._checks[name] = func

    def remove_check(self, name: str) -> None:
        self._checks.pop(name, None)
        self._remediations.pop(name, None)
        self._remediation_state.pop(name, None)
        self._pending_remediation.discard(name)

    def record_failure(self, name: str) -> None:
        self._failures[name] = self._failures.get(name, 0) + 1
        self._recent_failures.append(name)
        self._maybe_schedule_remediation(name)

    def record_success(self, name: str) -> None:
        self._failures.pop(name, None)
        if self._recent_failures:
            filtered = (item for item in self._recent_failures if item != name)
            self._recent_failures = deque(filtered, maxlen=self._recent_failures.maxlen)
        self._remediation_state.pop(name, None)
        self._pending_remediation.discard(name)

    def failure_counts(self) -> Dict[str, int]:
        return dict(self._failures)

    def register_remediation(self, name: str, func: RemediationCallable) -> None:
        """Register a remediation callback executed after repeated failures."""

        self._remediations[name] = func
        self._remediation_state.pop(name, None)

    async def run_checks(self) -> HealthReport:
        checks: Dict[str, HealthCheck] = {}
        overall_status = "healthy"
        for name, callback in self._checks.items():
            result = await _maybe_await(callback)
            check = self._normalise_result(name, result)
            failures = self._failures.get(name, 0)
            if failures >= self.max_failures and check.status == "healthy":
                check.status = "degraded"
                check.detail = (
                    f"Recovered after {failures} failures" if not check.detail else check.detail
                )
            if check.status == "unhealthy":
                overall_status = "unhealthy"
            elif check.status == "degraded" and overall_status != "unhealthy":
                overall_status = "degraded"
            checks[name] = check
        if self._recent_failures and overall_status == "healthy":
            overall_status = "degraded"
        if self._pending_remediation:
            await self._launch_pending_remediations()
        report = HealthReport(
            generated_at=datetime.now(timezone.utc),
            status=overall_status,
            checks=list(checks.values()),
        )
        return report

    def _normalise_result(self, name: str, result: CheckResult) -> HealthCheck:
        if isinstance(result, HealthCheck):
            return result
        if isinstance(result, dict):
            status = result.get("status", "healthy")
            detail = result.get("detail", "")
            return HealthCheck(name=name, status=status, detail=detail)
        if result:
            return HealthCheck(name=name, status="healthy")
        return HealthCheck(name=name, status="unhealthy", detail="check returned false")

    def remediation_history(self, limit: int = 10) -> List[str]:
        """Return recent remediation events for audit trails."""

        if limit <= 0:
            return []
        return list(self._recent_remediations)[-limit:]

    async def _launch_pending_remediations(self) -> None:
        tasks = [self._run_remediation(name) for name in list(self._pending_remediation)]
        if tasks:
            await asyncio.gather(*tasks)

    def _maybe_schedule_remediation(self, name: str) -> None:
        if name not in self._remediations:
            return
        failures = self._failures.get(name, 0)
        if failures < self.max_failures:
            return
        if self._remediation_state.get(name) == "running":
            return
        self._remediation_state[name] = "pending"
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self._pending_remediation.add(name)
        else:
            loop.create_task(self._run_remediation(name))

    async def _run_remediation(self, name: str) -> None:
        callback = self._remediations.get(name)
        if callback is None:
            self._pending_remediation.discard(name)
            self._remediation_state.pop(name, None)
            return
        self._remediation_state[name] = "running"
        try:
            result = callback()
            if isinstance(result, Awaitable):
                await result
            timestamp = datetime.now(timezone.utc).isoformat()
            self._recent_remediations.append(f"{timestamp}::{name}")
            LOGGER.info("Executed remediation for check %s", name)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Remediation for check %s failed", name)
        finally:
            self._pending_remediation.discard(name)
            self._remediation_state[name] = "completed"


async def _maybe_await(callback: CheckCallable) -> CheckResult:
    value = callback()
    if isinstance(value, Awaitable):
        awaitable_value: Awaitable[CheckResult] = value
        return await awaitable_value
    result_value: CheckResult = value
    return result_value
