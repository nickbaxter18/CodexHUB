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

Knowledge ingestion watchers are now opt-in: leave `KNOWLEDGE_WATCH_INTERVAL` blank to skip polling
and set it to a positive number to enable background reloads.

### 3. Run services

- **Express scaffolding**: `pnpm run dev` or `pnpm start` starts the Node entry point on port `4000`.
- **Editor health server**: `node backend/health-test.js` exposes `/health-test`, `/cursor-agent`,
  and `/task-status` guarded by `EDITOR_API_KEY`.
- **Python pipeline**: activate your virtual environment (created by `pnpm run setup`) and run the relevant modules,
  e.g. `python -m src.training.pipeline` or `python -m src.inference.service`. Detailed workflows
  live in `docs/usage.md`.

### 4. Cursor automation CLI

The consolidated CLI exposes all Cursor-focused automation through a single entry point:

```bash
python -m src.cursor.cli start --with-knowledge        # start auto-invocation + knowledge sync
python -m src.cursor.cli status                        # inspect compliance and usage metrics
python -m src.cursor.cli knowledge-refresh             # reload knowledge sources once without watchers
python -m src.cursor.cli rules                         # review auto-invocation rule stats
```

Existing `pnpm run cursor:*` scripts now forward to this CLI.

### 5. Quality checks

```bash
make quality       # orchestrate Node, docs, and Python quality suites with metrics capture
make quality-node  # run the Node.js subset with timing instrumentation
make quality-docs  # run Markdown/YAML/editorconfig linting with metrics
make quality-python # run pytest, governance validation, bandit, and pip audit with metrics
make format        # format JavaScript/TypeScript via Prettier and Python via black/isort
make lint          # run ESLint across Node workspaces
make lint-python   # run flake8 across Python packages
make typecheck     # run mypy against the expanded strict configuration
make test          # execute JavaScript/TypeScript unit tests
make test-python   # execute pytest suites
make security      # run npm and pip security audits
make cursor-status # emit Cursor automation health as JSON (non-zero exit on failure)
python -m src.common.config_loader --json  # validate pipeline/governance/metrics bundles
```

Each command is idempotent and suitable for CI usage; the aggregated `make quality` target mirrors
the GitHub Actions matrix and persists timing data under `results/performance/` for use with
`scripts/codex_status.py`. See `docs/usage.md` for additional workflow-specific helpers.

## Documentation

- [Setup Guide](docs/setup.md) – System requirements, environment bootstrapping, and dependency
  management.
- [Usage Guide](docs/usage.md) – Running services, orchestrating training, and common developer
  tasks.
- [API Reference](docs/api.md) – Available endpoints and CLI commands.
- [Architecture](docs/architecture.md) – High-level diagrams and module responsibilities.
- [Governance](docs/GOVERNANCE.md) – Fairness, privacy, and compliance controls.

## Security Notes

Hard-coded credentials have been removed in favor of environment variables. Rotate any previously
committed secrets and follow the guidance in `SECURITY.md` for secret management and operational
hardening.

## Contributing

Please review `CONTRIBUTING.md` and the checks listed above before opening a pull request. Run
`make quality` (or the narrower `quality-*` targets) locally to keep the mixed Node/Python toolchain
healthy.
