# Best Practices

_Last updated: 2024-12-04_

## Coding Standards

- **TypeScript/JavaScript**: Enforce ESLint + Prettier via Husky. Prefer named exports and
  immutable data structures. When side-effects are necessary, wrap them in functions that
  receive explicit dependencies to ease testing.
- **Python**: Run Ruff before committing. Align logging through `qa_engine/common/logging.py` and
  avoid global state; use dependency injection for services so QA harnesses can mock them.
- **Shell scripts**: Use `set -euo pipefail` and defensive quoting. Accept a configurable output
  directory where relevant so the scripts are composable in CI pipelines.

## Testing Strategy

- **Unit tests**: Co-locate tests in `tests/` with `.test.js/.ts` suffixes. Use Node's native
  test runner for JavaScript and `pytest` for Python packages. Always include failure-path
  coverage.
- **Integration tests**: House complex multi-service tests under `qa_engine/` and gate them behind
  explicit PNPM scripts so they can be opt-in for local runs.
- **Regression checks**: Update snapshot files deliberately and document any baseline changes in
  the PR description.

## Security & Compliance

- Run `scripts/run-quality-gates.sh pre-push` (or the equivalent pnpm script) before sharing
  branches; it executes linting, formatting, Node/Python tests, Semgrep, and Gitleaks scans.
- Review CodeQL and Semgrep alerts on every PR. Document mitigation steps for accepted risks in
  `SECURITY.md` or link to follow-up tickets.
- Store credentials exclusively in environment variables (`.env.example` documents expected
  variables). Use secret managers in production deployments.
- Capture remediation and AI review outcomes in `results/security/` and `results/ai-review/` so the
  governance loop in `docs/context/automation-pipeline.md` stays data-driven.

## Operational Practices

- Trigger Turbo tasks (`pnpm turbo run <task>`) to build only affected packages during CI or
  large refactors.
- Prefer `pnpm` scripts over raw binaries to ensure consistent tool versions.
- Keep context documentation updated when APIs, workflows, or quality gates change so that the
  fetch script distributes accurate guidance to downstream agents.
- Update `results/metrics/latest.json` via `scripts/metrics/collect_metrics.py` after major changes
  to capture build/test duration deltas and remediation cadence.
