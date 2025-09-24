import numpy as np
import pytest

from src.agents.decision_agent import DecisionAgent
from src.types import SimulationRequest


@pytest.mark.asyncio
async def test_decision_agent_selects_best_action() -> None:
    agent = DecisionAgent()
    np.random.seed(0)

    decision = await agent.act(
        {
            "actions": [
                {"name": "execute", "expected_reward": 0.9, "weight": 0.7},
                {"name": "skip", "expected_reward": 0.1, "weight": 0.3},
            ]
        }
    )
    assert decision["selected_action"] == "execute"
    assert decision["scores"]["execute"] > decision["scores"]["skip"]

    await agent.observe({"action": "execute", "outcome": 1})
    updated = await agent.act(
        {
            "actions": [
                {"name": "execute", "expected_reward": 0.5, "weight": 0.5},
                {"name": "skip", "expected_reward": 0.4, "weight": 0.5},
            ],
            "simulation": SimulationRequest(outcomes=[1.0, 0.0], probabilities=[0.7, 0.3], runs=10),
        }
    )
    assert updated["selected_action"] == "execute"
    assert updated["simulation"]["expected_value"] >= 0
