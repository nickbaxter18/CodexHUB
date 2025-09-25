# Contributing to the Governance-Integrated AI Pipeline

## Development Workflow
1. **Plan First:** Document module/file plans under `plans/` before implementation to maintain traceability.
2. **Follow Module Sections:** Every Python file must include the standard section headers (Purpose, Imports, Types, Logic, Error Handling, Performance, Exports) as demonstrated in new modules under `src/`.
3. **Configuration Updates:** When modifying YAML configs in `config/`, ensure corresponding Pydantic schemas in `src/common/config_loader.py` remain in sync.

## Testing Requirements
- Run `pytest` to execute unit, integration, and compliance suites covering training, registry, inference, fairness, and privacy.
- For JavaScript/TypeScript changes continue to follow existing npm-based workflows (see project README).
- Verify MLflow-dependent tests using local file-based stores; no external services are required.

## Governance Hooks
- Fairness thresholds are defined in `config/metrics.yaml`; updating them requires coordination with compliance stakeholders.
- Privacy policies live in `config/governance.yaml`; any changes must include documentation updates and test coverage in `tests/compliance`.

## Code Quality
- Use Ruff (`python -m ruff format` / `python -m ruff check`) as configured in `pyproject.toml`.
- Ensure no secrets are committed; use environment variables for production URIs.
- Update `CHANGELOG.md`, `ARCHITECTURE.md`, `SECURITY.md`, and `docs/GOVERNANCE.md` when introducing new governance-relevant functionality.
