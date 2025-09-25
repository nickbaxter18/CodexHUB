# Probabilistic QA Engine

## Purpose

Explain how probabilistic evaluation complements deterministic QA rules by introducing confidence-aware decisions, calibrated probabilities, and governance-aligned thresholds.

## Key Concepts

- **Distributions** – Metrics represented by mean and standard deviation to model variability.
- **Calibration** – Platt-scaling produces well-calibrated probabilities from historical QA outcomes.
- **Z-Scores** – Normalise thresholds relative to distribution parameters.
- **Pass Probability** – Converts z-scores to probabilities for comparisons against governance confidence targets.
- **Confidence Reports** – Summarise expected win-rate, Brier score, calibration error, and bootstrap confidence intervals.

## Usage

```python
from qa_engine import (
    confidence_report,
    evaluate_calibrated_metric,
    platt_calibration,
)

# Historical QA measurements and pass/fail outcomes
latency_scores = [240.0, 242.0, 238.0, 260.0, 280.0]
latency_passes = [1, 1, 1, 0, 0]
calibration = platt_calibration(latency_scores, latency_passes, min_samples=5)

# Evaluate a fresh latency value against Codex governance targets
passed, report, probability = evaluate_calibrated_metric(
    value=250.0,
    calibration=calibration,
    historical_scores=latency_scores,
    historical_labels=latency_passes,
    confidence=0.95,
)

print("Probability of passing:", probability)
print("Meets governance threshold:", passed)
print("Report:", report.as_dict())

# Generate a confidence report for dashboards or CI logs
dashboard_report = confidence_report(
    calibration.predict(latency_scores),
    latency_passes,
    confidence_level=0.95,
)
```

`config/qa_policies.json` defines target confidences for governed metrics. Updating those thresholds keeps CI enforcement and documentation in sync.

## CLI & Automation

- Run `python scripts/validate_configs.py` before commits to ensure probabilistic policies align with schemas (`qa_policies.json`),
  YAML overlays load correctly, and environment bundles remain valid.
- CI executes `tests/test_probabilistic_qa.py` and `tests/test_statistics_helpers.py` to verify statistical helpers, calibration logic, and governance alignment.

## Extension Ideas

- Support Bayesian updates when new samples arrive.
- Integrate percentile tracking for P99 latency budgets.
- Surface probability distributions within dashboard visualisations.
