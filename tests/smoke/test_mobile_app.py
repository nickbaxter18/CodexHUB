import asyncio
from types import SimpleNamespace

import pytest

from src.mobile import mobile_app


@pytest.mark.asyncio()
async def test_start_mobile_app_invokes_initialize(monkeypatch):
    called = False

    class DummyApp:
        async def initialize(self):
            nonlocal called
            called = True

    dummy = DummyApp()
    monkeypatch.setattr(mobile_app, "get_mobile_app", lambda: dummy)

    await mobile_app.start_mobile_app()
    assert called is True


@pytest.mark.asyncio()
async def test_mobile_goal_roundtrip(monkeypatch):
    class DummyGoal:
        def __init__(self):
            self.goal_id = "123"
            self.title = "Demo"
            self.description = "Desc"
            self.priority = SimpleNamespace(value="medium")
            self.approval_status = SimpleNamespace(value="pending")
            self.created_at = mobile_app.datetime.now()

    class DummyApp:
        async def create_goal(self, **_: str):
            return DummyGoal()

        async def get_goals(self, *_):
            return [DummyGoal()]

    dummy = DummyApp()
    monkeypatch.setattr(mobile_app, "get_mobile_app", lambda: dummy)

    created = await mobile_app.create_goal("Demo", "Desc")
    assert created["id"] == "123"
    assert created["status"] == "pending"

    goals = await mobile_app.get_goals()
    assert goals[0]["title"] == "Demo"

    await asyncio.sleep(0)
