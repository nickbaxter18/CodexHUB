from typing import Any

import pytest

from src.agents.ethics_agent import EthicsAgent
from src.errors import EthicsError


@pytest.mark.asyncio
async def test_ethics_agent_threshold(monkeypatch: Any) -> None:
    monkeypatch.setenv("RUNNER_FAIRNESS_THRESHOLD", "0.3")
    from src import config

    config.get_config.cache_clear()
    agent = EthicsAgent()

    approval = await agent.act({"risk": 0.1})
    assert approval["approved"]

    rejection = await agent.act({"risk": 0.9, "strict": False})
    assert not rejection["approved"]

    with pytest.raises(EthicsError):
        await agent.act({"risk": 0.9, "strict": True})

    config.get_config.cache_clear()
