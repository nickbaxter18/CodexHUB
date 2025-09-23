# Governance Configuration Guide

## Purpose

- Document the structure and intent of the machine-readable governance files located in `config/`.
- Provide editing and review guidance for engineers and governance stakeholders.

## Files

- `config/governance.json` – Arbitration priorities, trust thresholds, drift detection, fallback macros.
- `config/agents.json` – Agent responsibilities, permissions, and default trust scores.
- `config/qa_policies.json` – Metric budgets expressed as probabilistic thresholds.
- `config/qa_rules.json` – Detailed QA budgets, metrics, remediation macros, and macro schemas.

## Editing Workflow

1. Propose changes via Pull Request with context on the motivation and impact.
2. Run `python scripts/validate_configs.py` locally to verify schema compliance.
3. Tag the Meta Agent and QA reviewers for approval.
4. Update `CHANGELOG.md` and relevant ADRs describing governance shifts.

## Versioning

- Bump the `version` field in `governance.json` when arbitration priorities or trust thresholds change.
- Maintain semantic versioning for macros that appear in fallback mappings.

## Review Checklist

- [ ] Arbitration lists remain ordered by priority and cover all high-risk metrics.
- [ ] Trust multipliers keep scores within `[0.1, 1.5]` bounds.
- [ ] Drift detection thresholds balance sensitivity and noise.
- [ ] Fallback macro identifiers map to registered macros in macro registry.
- [ ] Agents gain explicit responsibilities and permissions.

## Escalation

- If conflicting governance changes land in parallel branches, the Meta Agent should raise a `governance_amendment` event for coordination.
- Disagreements on arbitration priorities require Architect + QA joint review before merge.
