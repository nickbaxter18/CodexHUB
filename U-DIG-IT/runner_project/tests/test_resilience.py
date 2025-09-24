import pytest

from src.utils.observer import HealthObserver


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
