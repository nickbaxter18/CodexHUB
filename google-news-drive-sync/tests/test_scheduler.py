import threading

import pytest

from src.scheduler import SchedulerHandle, schedule


def test_schedule_runs_job_with_fallback():
    calls = []
    done = threading.Event()

    def job():
        calls.append(object())
        done.set()

    handle = schedule(job, interval_minutes=0.001, scheduler=None)
    assert isinstance(handle, SchedulerHandle)
    assert done.wait(timeout=1)
    handle.shutdown()
    if handle.thread is not None:
        assert not handle.thread.is_alive()


def test_schedule_requires_configuration():
    with pytest.raises(ValueError):
        schedule(lambda: None, interval_minutes=0)


def test_schedule_with_custom_scheduler():
    class FakeScheduler:
        def __init__(self):
            self.jobs = []
            self.started = False
            self.removed = None
            self.shutdown_called = False

        def add_job(self, func, trigger, **kwargs):
            self.jobs.append((func, trigger, kwargs))

        def start(self):
            self.started = True

        def remove_job(self, job_id):
            self.removed = job_id

        def shutdown(self, wait):
            self.shutdown_called = True

    fake = FakeScheduler()

    handle = schedule(lambda: None, interval_minutes=1, scheduler=fake)

    assert fake.jobs
    assert fake.started
    assert handle.scheduler is fake

    handle.shutdown()
    assert fake.shutdown_called
