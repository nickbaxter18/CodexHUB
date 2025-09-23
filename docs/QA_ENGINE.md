# Probabilistic QA Engine

## Purpose

Explain how probabilistic evaluation complements deterministic QA rules by introducing confidence-aware decisions.

## Key Concepts

- **Distributions** – Metrics represented by mean and standard deviation to model variability.
- **Z-Scores** – Normalise thresholds relative to distribution parameters.
- **Pass Probability** – Converts z-scores to probabilities for comparisons against governance confidence targets.
- **Confidence Intervals** – Provide bounds on expected metric behaviour for planning.

## Usage

```python
from qa_engine import evaluate_metric

latency_distribution = {"mean": 240.0, "std": 25.0}
if evaluate_metric(255.0, latency_distribution, confidence=0.95):
    print("Latency within expectations")
else:
    print("Investigate latency regression")
```

## CLI & Automation

- Run `python scripts/validate_configs.py` before commits to ensure probabilistic policies align with schemas.
- CI executes `tests/test_probabilistic_qa.py` to verify statistical helpers.

## Extension Ideas

- Support Bayesian updates when new samples arrive.
- Integrate percentile tracking for P99 latency budgets.
- Surface probability distributions within dashboard visualisations.
