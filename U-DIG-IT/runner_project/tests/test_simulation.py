import numpy as np

from src.decision import simulation


def test_monte_carlo_expectation_produces_reasonable_value() -> None:
    np.random.seed(1)
    expectation = simulation.monte_carlo_expectation([1.0, 0.0], [0.75, 0.25], runs=200)
    assert 0.6 < expectation < 0.9


def test_markov_chain_simulation_length() -> None:
    np.random.seed(1)
    transitions = {
        "idle": {"idle": 0.5, "run": 0.5},
        "run": {"idle": 0.3, "run": 0.7},
    }
    path = simulation.simulate_markov_chain(transitions, initial_state="idle", steps=5)
    assert len(path) >= 2
    assert path[0] == "idle"
