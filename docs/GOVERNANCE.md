# Governance Guide

This document unifies governance **configuration guidelines** and **integration practices**.
It covers both the structure and process for maintaining governance configuration files, as well as technical integration of fairness, privacy, and registry controls.

---

## Governance Configuration Guide

### Purpose

- Document the structure and intent of the machine-readable governance files located in `config/`.
- Provide editing and review guidance for engineers and governance stakeholders.

### Files

- `config/governance.json` – Arbitration priorities, trust thresholds, operational drift guardrails, fallback macros.
- `config/agents.json` – Agent responsibilities, permissions, and default trust scores.
- `config/qa_policies.json` – Metric budgets expressed as probabilistic thresholds.
- `config/qa_rules.json` – Detailed QA budgets, metrics, remediation macros, and macro schemas.
- `config/drift.json` – Statistical drift reference windows and PSI/KS/KL enforcement thresholds.

### Editing Workflow

1. Propose changes via Pull Request with context on the motivation and impact.
2. Run `python scripts/validate_configs.py` locally to verify schema compliance.
3. Tag the Meta Agent and QA reviewers for approval.
4. Update `CHANGELOG.md` and relevant ADRs describing governance shifts.

### Versioning

- Bump the `version` field in `governance.json` when arbitration priorities or trust thresholds change.
- Maintain semantic versioning for macros that appear in fallback mappings.

### Review Checklist

- [ ] Arbitration lists remain ordered by priority and cover all high-risk metrics.
- [ ] Trust multipliers keep scores within `[0.1, 1.5]` bounds.
- [ ] Drift detection thresholds balance sensitivity and noise (PSI, KS, KL).
- [ ] Fallback macro identifiers map to registered macros in macro registry.
- [ ] Agents gain explicit responsibilities and permissions.

### Escalation

- If conflicting governance changes land in parallel branches, the Meta Agent should raise a `governance_amendment` event for coordination.
- Disagreements on arbitration priorities require Architect + QA joint review before merge.

---

## Governance Integration Overview

### Configuration Controls

- **Config Validation:** `meta_agent/config_loader.py` validates JSON governance assets (`governance.json`, `qa_policies.json`, `qa_rules.json`, and `drift.json`) against the schemas in `config/*.schema.json`. The `scripts/validate_configs.py` helper runs these checks locally and in CI.
- **Governance Thresholds:** Metric and fairness thresholds declared in `config/metrics.yaml` are consumed by `src/training/metrics.py` and `src/governance/fairness.py` during evaluation.

### Fairness Management

- **Evaluation Logic:** `src/governance/fairness.py` computes statistical parity difference, equal opportunity difference, and disparate impact ratios. Enforcement is controlled via `fairness.enforce` and `fairness.min_samples_per_group` in `config/governance.yaml`.
- **Testing:** `tests/compliance/test_fairness.py` verifies fairness metrics pass when within thresholds and raises on insufficient data, providing regression coverage.

### Privacy Management

- **PII Scrubbing:** `src/governance/privacy.py` removes blocked PII tokens. Configuration for allowed/blocked patterns resides in `config/governance.yaml` and is validated in `tests/compliance/test_privacy.py`.

### Registry & Auditability

- **MLflow Registry Wrapper:** `src/registry/registry.py` ensures experiments exist, metrics/params logged, and model versions retrievable. Integration tests (`tests/unit/test_registry.py`, `tests/integration/test_inference_pipeline.py`) confirm registry behaviour.
- **Audit Artefacts:** MLflow runs store lineage data enabling future audit exports. Model URIs feed into inference caching for traceability.

### Inference Governance

- **Payload Validation:** `src/inference/inference.py` validates requests via Pydantic schemas and enforces concurrency + batch-size budgets.
- **Monitoring Hooks:** The inference service exposes caching TTL and concurrency controls, preparing for upcoming monitoring modules.

### Contribution Checklist

1. Update relevant configs and ensure `pytest` passes.
2. Extend governance tests when adding new fairness/ privacy features.
3. Document architectural or policy changes in `ARCHITECTURE.md`, `SECURITY.md`, `ROADMAP.md`, and this governance guide.