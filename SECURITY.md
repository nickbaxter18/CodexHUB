# Security Considerations for the AI Production Pipeline

## Threat Model Updates

- **Config Integrity:** All YAML configs are now validated with Pydantic via `src/common/config_loader`, reducing risk of malicious overrides or malformed parameters.
- **Registry Interactions:** `src/registry/registry.py` enforces experiment creation and wraps MLflow errors, preventing silent failures that could expose stale or insecure models.
- **Inference Controls:** `src/inference/inference.py` applies bounded semaphores and cache TTLs, mitigating denial-of-service risks from excessive concurrent prediction requests.

## Data Protection

- **PII Scrubbing:** `src/governance/privacy.py` scrubs e-mails, phone numbers, and SSNs before artefacts reach logs or documentation. Allowlists enable safe exceptions while maintaining compliance defaults.
- **Fairness Enforcement:** Governance thresholds in `config/metrics.yaml` and `config/governance.yaml` prevent deploying biased models by failing CI compliance tests when fairness metrics drift.

## Operational Safeguards

- **No Secrets in Repo:** All registry URIs and experiment names are plain-text development defaults. Production deployments must source URIs via environment variables or secret managers.
- **Auditability:** MLflow registry usage centralises run metadata, supporting future audit trails and alignment with GDPR/CCPA.
- **Testing:** Comprehensive unit, integration, and compliance tests (see `tests/`) enforce behaviour for malformed inputs, fairness coverage, and privacy guarantees.
