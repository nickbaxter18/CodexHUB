"""Decision agent coordinating probabilistic reasoning."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from ..decision import bayes, mdp, simulation
from ..errors import DecisionError
from ..types import SimulationRequest
from .base import Agent


class DecisionAgent(Agent):
    """Select actions using Bayesian updates and MDP guidance."""

    def __init__(self) -> None:
        super().__init__(name="decision")
        self._bandit_state: Dict[str, Tuple[float, float]] = defaultdict(lambda: (1.0, 1.0))
        self._last_action: Dict[str, str] = {}

    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        action = context.get("action")
        outcome = context.get("outcome")
        if action and isinstance(outcome, (int, float)):
            alpha, beta_param = self._bandit_state[action]
            successes = 1 if outcome > 0 else 0
            failures = 1 - successes
            self._bandit_state[action] = bayes.beta_update(alpha, beta_param, successes, failures)
        return context

    async def act(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        actions: List[Dict[str, Any]] = payload.get("actions", [])
        if not actions:
            raise DecisionError("Decision agent requires at least one candidate action")

        action_values: Dict[str, float] = {}
        for descriptor in actions:
            name = descriptor.get("name")
            if not name:
                raise DecisionError("Each action descriptor requires a name")
            prior = self._bandit_state[name]
            prior_mean = bayes.beta_mean(*prior)
            expected_reward = float(descriptor.get("expected_reward", prior_mean))
            weight = float(descriptor.get("weight", 1.0))
            combined = bayes.bayesian_weighted_average(
                [expected_reward, prior_mean], [weight, 1 - min(weight, 1)]
            )
            action_values[name] = combined

        chosen = mdp.epsilon_greedy(action_values, epsilon=float(payload.get("epsilon", 0.05)))
        self._last_action[payload.get("task_id", "global")] = chosen

        sim_request = payload.get("simulation")
        simulation_summary = None
        if isinstance(sim_request, SimulationRequest):
            samples = simulation.monte_carlo_expectation(
                sim_request.outcomes,
                sim_request.probabilities,
                runs=sim_request.runs,
            )
            simulation_summary = {"expected_value": samples}

        return {
            "selected_action": chosen,
            "scores": action_values,
            "simulation": simulation_summary,
        }
