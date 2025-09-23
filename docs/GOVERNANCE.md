# Governance Integration Overview

## Configuration Controls

- **Config Validation:** `src/common/config_loader.py` defines Pydantic schemas for all YAML configurations under `config/`. CI should load `config/default.yaml`, `config/metrics.yaml`, and `config/governance.yaml` to ensure schema compliance before merges.
- **Governance Thresholds:** Metric and fairness thresholds declared in `config/metrics.yaml` are consumed by `src/training/metrics.py` and `src/governance/fairness.py` during evaluation.

## Fairness Management

- **Evaluation Logic:** `src/governance/fairness.py` computes statistical parity difference, equal opportunity difference, and disparate impact ratios. Enforcement is controlled via `fairness.enforce` and `fairness.min_samples_per_group` in `config/governance.yaml`.
- **Testing:** `tests/compliance/test_fairness.py` verifies fairness metrics pass when within thresholds and raises on insufficient data, providing regression coverage.

## Privacy Management

- **PII Scrubbing:** `src/governance/privacy.py` removes blocked PII tokens. Configuration for allowed/blocked patterns resides in `config/governance.yaml` and is validated in `tests/compliance/test_privacy.py`.

## Registry & Auditability

- **MLflow Registry Wrapper:** `src/registry/registry.py` ensures experiments exist, metrics/params logged, and model versions retrievable. Integration tests (`tests/unit/test_registry.py`, `tests/integration/test_inference_pipeline.py`) confirm registry behaviour.
- **Audit Artefacts:** MLflow runs store lineage data enabling future audit exports. Model URIs feed into inference caching for traceability.

## Inference Governance

- **Payload Validation:** `src/inference/inference.py` validates requests via Pydantic schemas and enforces concurrency + batch-size budgets.
- **Monitoring Hooks:** The inference service exposes caching TTL and concurrency controls, preparing for upcoming monitoring modules.

## Contribution Checklist

1. Update relevant configs and ensure `pytest` passes.
2. Extend governance tests when adding new fairness/ privacy features.
3. Document architectural or policy changes in `ARCHITECTURE.md`, `SECURITY.md`, `ROADMAP.md`, and this governance guide.
