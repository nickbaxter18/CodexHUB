# Getting Started Guide

_Last updated: 2024-11-23_

This guide summarises the minimum steps required to prepare a local development environment or a
fresh CI runner for CodexHUB.

## Prerequisites

- Node.js 20+
- pnpm 9+ (`corepack enable pnpm`)
- Python 3.11 with `pipx` (for `pip-audit` and auxiliary tooling)
- Docker (optional) for running dependent services in integration tests

## Bootstrap

```bash
pnpm install
pnpm run setup             # installs Python deps and validates configs
python scripts/auto_setup_cursor.py  # optional: ensures Cursor integration
```

## Quality Gates

Run these commands locally before opening a pull request. They mirror the automated Husky pipeline.

```bash
pnpm lint
pnpm test
pnpm run typecheck
pnpm run scan:secrets      # gitleaks full-history scan
pnpm turbo run build --filter=...
```

## CI & Deployment

- **GitHub Actions**: CI entrypoint is `.github/workflows/ci.yml`. Security gates live in
  `security-pr.yml` and `codeql.yml`.
- **Turbo**: Use `pnpm turbo run <task>` to execute graph-aware builds/tests across workspaces. The
  pipeline definition is stored in `turbo.json`.
- **Docker**: `docker-compose.yml` orchestrates optional local services when running E2E tests.

## Troubleshooting

- Review `TROUBLESHOOTING_SETUP.md` for known issues across major platforms.
- Run `pnpm doctor` and `python scripts/validate_configs.py` to diagnose dependency or config
  drift.
- For Cursor integration problems, execute `pnpm cursor:validate` to confirm compliance state.
