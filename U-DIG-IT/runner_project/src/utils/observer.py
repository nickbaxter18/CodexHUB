"""Health and resilience utilities for Stage 3."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Awaitable, Callable, Deque, Dict, Union

from ..types import HealthCheck, HealthReport
from .logger import get_logger

LOGGER = get_logger("observer")

CheckResult = Union[bool, HealthCheck, Dict[str, str]]
CheckCallable = Callable[[], Union[CheckResult, Awaitable[CheckResult]]]


class HealthObserver:
    """Track health checks and repeated failures for auto-healing."""

    def __init__(self, max_failures: int = 3) -> None:
        self._checks: Dict[str, CheckCallable] = {}
        self._failures: Dict[str, int] = {}
        self._recent_failures: Deque[str] = deque(maxlen=20)
        self.max_failures = max_failures

    def register_check(self, name: str, func: CheckCallable) -> None:
        self._checks[name] = func

    def remove_check(self, name: str) -> None:
        self._checks.pop(name, None)

    def record_failure(self, name: str) -> None:
        self._failures[name] = self._failures.get(name, 0) + 1
        self._recent_failures.append(name)

    def record_success(self, name: str) -> None:
        self._failures.pop(name, None)
        if self._recent_failures:
            filtered = (item for item in self._recent_failures if item != name)
            self._recent_failures = deque(filtered, maxlen=self._recent_failures.maxlen)

    def failure_counts(self) -> Dict[str, int]:
        return dict(self._failures)

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


async def _maybe_await(callback: CheckCallable) -> CheckResult:
    value = callback()
    if isinstance(value, Awaitable):
        awaitable_value: Awaitable[CheckResult] = value
        return await awaitable_value
    result_value: CheckResult = value
    return result_value
