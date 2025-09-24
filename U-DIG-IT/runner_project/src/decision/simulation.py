"""Simulation helpers supporting the decision agent."""

from __future__ import annotations

from typing import Callable, List, Mapping, Sequence

import numpy as np

from ..errors import DecisionError


def monte_carlo_expectation(
    outcomes: Sequence[float],
    probabilities: Sequence[float],
    runs: int = 100,
) -> float:
    if runs <= 0:
        raise DecisionError("Number of Monte Carlo runs must be positive")
    probs = np.asarray(probabilities, dtype=float)
    values = np.asarray(outcomes, dtype=float)
    if probs.size != values.size:
        raise DecisionError("Outcomes and probabilities must be the same length")
    if probs.sum() <= 0:
        raise DecisionError("Probabilities must sum to a positive value")
    probs = probs / probs.sum()
    samples = np.random.choice(values, size=runs, p=probs)
    return float(samples.mean())


def simulate_markov_chain(
    transition_matrix: Mapping[str, Mapping[str, float]],
    initial_state: str,
    steps: int,
) -> List[str]:
    if steps <= 0:
        raise DecisionError("Steps must be positive")
    if initial_state not in transition_matrix:
        raise DecisionError(f"Unknown initial state: {initial_state}")
    states = [initial_state]
    current = initial_state
    for _ in range(steps):
        transitions = transition_matrix.get(current)
        if not transitions:
            break
        next_states = list(transitions.keys())
        probabilities = np.asarray(list(transitions.values()), dtype=float)
        if probabilities.sum() <= 0:
            raise DecisionError("Transition probabilities must sum to a positive value")
        probabilities = probabilities / probabilities.sum()
        current = str(np.random.choice(next_states, p=probabilities))
        states.append(current)
    return states


def run_batched_simulation(
    scenario_factory: Callable[[int], Sequence[float]],
    runs: int,
) -> List[float]:
    if runs <= 0:
        raise DecisionError("Simulation runs must be positive")
    outcomes: List[float] = []
    for index in range(runs):
        scenario = scenario_factory(index)
        if not scenario:
            raise DecisionError("Scenario factory returned no outcomes")
        outcomes.append(float(np.mean(scenario)))
    return outcomes
