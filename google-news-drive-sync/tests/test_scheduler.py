import time

import pytest

from src.scheduler import schedule


def test_schedule_runs_job():
    calls = []

    def job():
        calls.append(time.time())
        if len(calls) >= 1:
            thread.stop_event.set()  # type: ignore[attr-defined]

    thread = schedule(job, 0.001)
    thread.join(timeout=1)

    assert calls
    assert not thread.is_alive()


def test_schedule_requires_positive_interval():
    with pytest.raises(ValueError):
        schedule(lambda: None, 0)
