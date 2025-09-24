# Security Considerations for the AI Production Pipeline

## Threat Model Updates

- **Config Integrity:** All YAML configs are now validated with Pydantic via `src/common/config_loader`, reducing risk of malicious overrides or malformed parameters.
- **Registry Interactions:** `src/registry/registry.py` enforces experiment creation and wraps MLflow errors, preventing silent failures that could expose stale or insecure models.
- **Inference Controls:** `src/inference/inference.py` applies bounded semaphores and cache TTLs, mitigating denial-of-service risks from excessive concurrent prediction requests.

## Data Protection

- **PII Scrubbing:** `src/governance/privacy.py` scrubs e-mails, phone numbers, and SSNs before artefacts reach logs or documentation. Allowlists enable safe exceptions while maintaining compliance defaults.
- **Fairness Enforcement:** Governance thresholds in `config/metrics.yaml` and `config/governance.yaml` prevent deploying biased models by failing CI compliance tests when fairness metrics drift.

## Operational Safeguards

- **Secret management:** All runtime credentials (including the editor health-test API key) must be injected via environment variables or an external secret manager. The repository no longer contains hard-coded keys—rotate any keys that previously lived in source control.
- **No Secrets in Repo:** Keep `.env` files out of version control and rely on deployment-specific secret storage (e.g. Doppler, Vault, GitHub Actions secrets).
- **Auditability:** MLflow registry usage centralises run metadata, supporting future audit trails and alignment with GDPR/CCPA.
- **Testing:** Comprehensive unit, integration, and compliance tests (see `tests/`) enforce behaviour for malformed inputs, fairness coverage, and privacy guarantees.

## Cross-platform hygiene

- Development helpers in `backend/` now avoid Windows-only paths. When extending automation scripts, prefer relative paths or configurable environment variables to maintain compatibility across Linux, macOS, and Windows environments.
