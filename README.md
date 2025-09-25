# CodexHUB

CodexHUB is a hybrid Node.js and Python workspace for building, governing, and serving AI-assisted
developer workflows. The repository pairs an Express-based orchestration layer with a schema-driven
Python ML pipeline that handles ingestion, training, governance, and inference.

## Repository Layout

- `src/` – Node services, Express entry points, and shared utilities.
- `apps/` – End-user web experiences.
  - `apps/editor/` – The AGENTS.md documentation site (Next.js).
- `backend/` – Development helpers for the web-based Codex editor and local automation hooks.
- `packages/automation/` – Python automation stacks (agents, macro system, meta-agent, QA engine)
  surfaced as a normalized workspace. Legacy import paths remain available for compatibility.
- `rentalos-ai/` – Experimental AI-assisted rental operations workspace (Vite front end).
- `qa/`, `tests/` – Quality gates, governance checks, and automated verification suites.
- `docs/` – Living documentation for setup, API usage, governance, and architecture.
- `scripts/` – Automation helpers for Cursor, knowledge ingestion, and repo health checks.

## Prerequisites

- Node.js 20+
- pnpm 8+ (Corepack users can enable with `corepack enable`)
- Python 3.11 with `pip` (virtual environments recommended)
- [pre-commit](https://pre-commit.com/) for enforcing mixed-language formatting locally
- Optional: Docker 24+ for containerized deployments

## Getting Started

### 1. Install dependencies

```bash
pnpm run setup
```

The bootstrap script installs Node dependencies, provisions a `.venv` virtual environment, installs
both runtime and development Python requirements, and wires up `husky`/`pre-commit` hooks. Pass
`--skip-node`, `--skip-python`, or `--no-dev-extras` to customise the workflow when you only need a
subset of the toolchain. If you want to hydrate additional pnpm workspaces (for example
`apps/editor` or `rentalos-ai`), follow up with filtered installs such as
`pnpm install --filter apps/editor...`.

### 2. Configure environment variables

Copy `.env.example` into `.env` and adjust the values to match your environment. Regenerate the
example file with `pnpm run env:example` whenever environment variables change to keep
documentation, automation, and templates aligned. Curated profiles now live under
`config/environments/` (`development.env`, `cursor.env`, `ci.env`) so you can quickly swap between a
minimal setup and the Cursor-heavy automation stack. Review `docs/setup.md` for a complete option
reference and avoid committing secrets.

The repository now publishes a machine-readable schema at `config/env.schema.json`. Use the shared
validator to confirm that all required values (and their defaults) are present before committing:

```bash
python -m src.common.config_loader --env .env --env config/environments/ci.env --json
```

When schema changes are required, regenerate the artifact with:

```bash
python scripts/generate_env_schema.py
```

Knowledge ingestion watchers are now opt-in: leave `KNOWLEDGE_WATCH_INTERVAL` blank to skip polling
and set it to a positive number to enable background reloads.

#### Cursor automation presets

- **Minimal (default)** – keep all Cursor toggles disabled (`CURSOR_AUTO_INVOCATION_ENABLED=false`,
  `KNOWLEDGE_AUTO_LOAD=false`, etc.) and rely on manual commands when you need automation.
- **Cursor-first** – start from `config/environments/cursor.env` or set the Cursor toggles in your
  `.env` to `true` to enable continuous knowledge syncing, auto-invocation, and mobile controls.

### 3. Manage knowledge datasets

Store optional NDJSON bundles under `data/knowledge/` so they can be pruned independently of the
repository history. The default configuration looks for:

- `Brain docs cleansed .ndjson`
- `Bundle cleansed .ndjson`
- `data/knowledge/*.ndjson`

When sharing the project, keep the directory structure but omit large datasets unless a teammate
explicitly needs them.

### 4. Run services

- **Express scaffolding**: `pnpm run dev` or `pnpm start` starts the Node entry point on port `4000`.
- **Editor health server**: `node backend/health-test.js` exposes `/health-test`, `/cursor-agent`,
  and `/task-status` guarded by `EDITOR_API_KEY`.
- **Python pipeline**: activate your virtual environment (created by `pnpm run setup`) and run the relevant modules,
  e.g. `python -m src.training.pipeline` or `python -m src.inference.service`. Detailed workflows
  live in `docs/usage.md`.

### 5. Cursor automation CLI

The consolidated CLI exposes all Cursor-focused automation through a single entry point:

```bash
python -m src.cursor.cli start --with-knowledge        # start auto-invocation + knowledge sync
python -m src.cursor.cli status                        # inspect compliance and usage metrics
python -m src.cursor.cli knowledge-refresh             # reload knowledge sources once without watchers
python -m src.cursor.cli rules                         # review auto-invocation rule stats
```

Existing `pnpm run cursor:*` scripts now forward to this CLI.

### 6. Quality checks

```bash
make quality       # orchestrate Node, docs, and Python quality suites with metrics capture
make quality-node  # run the Node.js subset with timing instrumentation
make quality-docs  # run Markdown/YAML/editorconfig linting with metrics
make quality-python # run pytest, governance validation, bandit, and pip audit with metrics
make format        # format JavaScript/TypeScript via Prettier and Python via Ruff
make lint          # run ESLint across Node workspaces
make lint-python   # run Ruff across Python packages
make typecheck     # run mypy against the expanded strict configuration
make test          # execute JavaScript/TypeScript unit tests
make test-python   # execute pytest suites
make security      # run npm and pip security audits
make cursor-status # emit Cursor automation health as JSON (non-zero exit on failure)
scripts/run-quality-gates.sh pre-push   # Husky-equivalent gate (lint, format, tests, Semgrep, Gitleaks)
python scripts/metrics/collect_metrics.py --skip-commands  # refresh governance metrics snapshot
python -m src.common.config_loader --json  # validate pipeline/governance/metrics bundles
python -m src.performance.cli node-quality --skip "pnpm audit" --max-workers 2  # targeted quality run
```

Each command is idempotent and suitable for CI usage; the aggregated `make quality` target mirrors
the GitHub Actions matrix and now persists timing data under `results/metrics/` (for cross-language
durations) and `results/performance/` (for Cursor agents). See `docs/usage.md` and
`docs/context/continuous-improvement.md` for additional workflow-specific helpers.

### 7. Fetch repository context

Use the Context Hub to gather a curated snapshot of architecture and governance docs for humans or
automated agents. The fetch script copies the latest guidance into a portable bundle:

```bash
./scripts/fetch-context.sh .context-bundle --archive
ls .context-bundle
cat .context-bundle/context-manifest.json
ls .context-bundle.tar.gz
```

Update the documents under `docs/context/` whenever new architecture patterns or runbooks are
introduced so the exported bundle remains authoritative. The optional archive flag packages the
bundle as `context-bundle.tar.gz` so agents can download a single artifact.

## Documentation

- [Setup Guide](docs/setup.md) – System requirements, environment bootstrapping, and dependency
  management.
- [Usage Guide](docs/usage.md) – Running services, orchestrating training, and common developer
  tasks.
- [API Reference](docs/api.md) – Available endpoints and CLI commands.
- [Architecture](docs/architecture.md) – High-level diagrams and module responsibilities.
- [Governance](docs/GOVERNANCE.md) – Fairness, privacy, and compliance controls.
- [Context Hub](docs/context/README.md) – Aggregated design patterns, onboarding runbooks, automation playbooks, and AI review procedures.

## Automated Quality Gates

Husky manages the local Git hooks and delegates linting, formatting, unit tests, and security
scans through `scripts/run-quality-gates.sh`. The pre-commit hook wraps `lint-staged` and the Python
pre-commit suite (which includes pnpm tests and pytest), while the pre-push hook executes linting,
format checks, pnpm tests, type-checking, pytest, Semgrep (SAST), and a full-history Gitleaks scan.
Commit message validation is enforced via the `commit-msg` hook.

To refresh the hooks after cloning or when tooling changes:

```bash
pnpm install
pnpm run prepare
```

To run the same checks manually (for example, on CI agents without Husky), invoke:

```bash
scripts/run-quality-gates.sh pre-commit
scripts/run-quality-gates.sh pre-push
```

Secret scanning can be executed on demand across the entire Git history with either the Husky
pre-push hook or a standalone command:

```bash
pnpm run scan:secrets            # writes SARIF to results/security/gitleaks-report.sarif
```

The scheduled GitHub Actions security workflow now executes the same `scripts/scan-secrets.sh`
wrapper weekly and uploads the SARIF report alongside audit, Bandit, CodeQL, and Snyk scans so
leaked credentials are surfaced even when developers forget to run the hook locally.

Set `GITLEAKS_TOKEN` or configure Docker if you prefer running the official container image. Semgrep rules come from the `p/security-audit` policy; customise via `.semgrep.yml` if the default set is too noisy.

## Security Notes

Hard-coded credentials have been removed in favor of environment variables. Rotate any previously
committed secrets and follow the guidance in `SECURITY.md` for secret management and operational
hardening.

## Contributing

Please review `CONTRIBUTING.md` and the checks listed above before opening a pull request. Run
`make quality` (or the narrower `quality-*` targets) locally to keep the mixed Node/Python toolchain
healthy.
