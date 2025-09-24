"""Markov Decision Process helpers for the decision agent."""

from __future__ import annotations

from typing import Dict, Mapping, Sequence, Tuple

import numpy as np

from ..errors import DecisionError

State = str
Action = str
Transition = Mapping[State, float]
TransitionModel = Mapping[State, Mapping[Action, Transition]]
RewardModel = Mapping[State, Mapping[Action, float]]


def value_iteration(
    states: Sequence[State],
    actions: Sequence[Action],
    transition_model: TransitionModel,
    reward_model: RewardModel,
    discount: float = 0.9,
    tolerance: float = 1e-4,
    max_iterations: int = 200,
) -> Tuple[Dict[State, float], Dict[State, Action]]:
    """Compute optimal state values and policy via value iteration."""

    if not 0 <= discount < 1:
        raise DecisionError("Discount factor must be in [0, 1)")
    values = {state: 0.0 for state in states}
    for _ in range(max_iterations):
        delta = 0.0
        for state in states:
            action_values = []
            for action in actions:
                transitions = transition_model.get(state, {}).get(action)
                reward = reward_model.get(state, {}).get(action)
                if transitions is None or reward is None:
                    continue
                total = 0.0
                for next_state, probability in transitions.items():
                    if probability < 0:
                        raise DecisionError("Transition probabilities must be non-negative")
                    total += probability * values.get(next_state, 0.0)
                action_values.append(reward + discount * total)
            if not action_values:
                continue
            best = max(action_values)
            delta = max(delta, abs(best - values[state]))
            values[state] = best
        if delta < tolerance:
            break

    policy: Dict[State, Action] = {}
    for state in states:
        best_action = None
        best_value = float("-inf")
        for action in actions:
            transitions = transition_model.get(state, {}).get(action)
            reward = reward_model.get(state, {}).get(action)
            if transitions is None or reward is None:
                continue
            total = 0.0
            for next_state, probability in transitions.items():
                total += probability * values.get(next_state, 0.0)
            candidate_value = reward + discount * total
            if candidate_value > best_value:
                best_value = candidate_value
                best_action = action
        if best_action is not None:
            policy[state] = best_action
    return values, policy


def epsilon_greedy(values: Mapping[Action, float], epsilon: float = 0.1) -> Action:
    """Select an action using an epsilon-greedy policy."""

    if not values:
        raise DecisionError("No actions provided to epsilon_greedy")
    if not 0 <= epsilon <= 1:
        raise DecisionError("Epsilon must be in [0, 1]")
    actions = list(values.keys())
    rewards = np.asarray([values[action] for action in actions], dtype=float)
    if np.random.random() < epsilon:
        return str(np.random.choice(actions))
    max_value = np.max(rewards)
    best_actions = [action for action, reward in zip(actions, rewards) if reward == max_value]
    return str(np.random.choice(best_actions))
