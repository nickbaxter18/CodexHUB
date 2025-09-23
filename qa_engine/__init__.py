"""Probabilistic QA engine package exposing uncertainty-aware utilities."""

# === Header & Purpose ===
# Aggregates helper modules that interpret QA metrics as probability
# distributions for trust-aware decision making.

from .probabilistic_qa import evaluate_metric, pass_probability, z_score
from .statistics_helpers import mean_confidence_interval, percentile, sample_mean_std

__all__ = [
    "evaluate_metric",
    "pass_probability",
    "z_score",
    "mean_confidence_interval",
    "percentile",
    "sample_mean_std",
]
