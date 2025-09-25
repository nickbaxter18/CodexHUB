# CodexHUB Governance-Integrated AI Production Pipeline — Iteration Plan

## Intent & Constraints

- **Purpose:** Establish the foundational modules for a governance-aware ML production pipeline covering configuration management, data loading, metrics, fairness, privacy, registry integration, and inference.
- **Business Value:** Enables reproducible, transparent, and compliant ML workflows aligning with CodexHUB governance artifacts.
- **Constraints:** Python 3.11, MLflow-based registry (file-backed for local dev), PyTorch/TF agnostic architecture, zero secrets in repo, configs via YAML with schema validation.

## File Map

- `config/`
  - `default.yaml` — Global training/inference defaults.
  - `metrics.yaml` — Thresholds for core and fairness metrics.
  - `governance.yaml` — Governance rules for privacy, fairness, monitoring.
- `src/common/`
  - `config_loader.py` — Shared YAML parsing + Pydantic validation utilities.
  - `README.md` — Module overview and usage notes.
- `src/training/`
  - `__init__.py` — Package export surface.
  - `README.md` — Training module overview.
  - `data_loader.py` — Dataset ingestion + validation.
  - `metrics.py` — Core evaluation metrics.
- `src/governance/`
  - `__init__.py`
  - `README.md`
  - `fairness.py` — Bias evaluation utilities.
  - `privacy.py` — PII scrubbing and compliance guards.
- `src/registry/`
  - `__init__.py`
  - `README.md`
  - `registry.py` — MLflow integration layer.
- `src/inference/`
  - `__init__.py`
  - `README.md`
  - `inference.py` — Canonical inference logic with model caching.
- `tests/`
  - `unit/test_config_loader.py`
  - `unit/test_data_loader.py`
  - `unit/test_metrics.py`
  - `unit/test_registry.py`
  - `integration/test_inference_pipeline.py`
  - `compliance/test_fairness.py`
  - `compliance/test_privacy.py`
- `docs/GOVERNANCE.md` — Updated to link new modules.
- Root governance docs (`ARCHITECTURE.md`, `SECURITY.md`, `CONTRIBUTING.md`, `ROADMAP.md`) — Updated with pipeline references.
- `CHANGELOG.md` — Document iteration summary.
- `requirements.txt` — Runtime dependencies.

## Dependencies & Tooling

- Libraries: `mlflow`, `pydantic`, `pandas`, `numpy`, `scikit-learn`, `pyyaml`.
- Testing: `pytest` with tmp paths and fixtures for mlflow file-backed store.
- Formatting: `ruff format` + `ruff check` (already configured in repo).

## Risk & Mitigation Notes

- **MLflow Dependency Weight:** Use local file-backed store in tests to avoid network use.
- **Data Privacy:** Ensure scrubbing functions handle common PII patterns and document limitations.
- **Fairness Metrics:** Provide deterministic calculations with explicit threshold handling to avoid flaky compliance tests.
- **Config Validation:** Enforce schema to prevent silent misconfiguration.

## Exit Criteria for This Iteration

1. All listed modules and configs created with complete section documentation.
2. Tests cover happy paths, error paths, and governance compliance checks.
3. Governance documents updated to describe new capabilities and enforcement hooks.
4. `pytest` passes locally.
