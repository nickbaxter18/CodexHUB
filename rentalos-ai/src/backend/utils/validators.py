"""Input validators and fairness checks."""

from __future__ import annotations


def fairness_check(credit_score: int, income: float) -> bool:
    """Return True when the evaluation respects baseline fairness constraints."""

    return credit_score >= 550 or income > 40000
