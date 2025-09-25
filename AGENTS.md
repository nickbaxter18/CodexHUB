# CodexHUB Agent Directives

## Workspace Rules

- Use **pnpm** for all Node.js/TypeScript packages. Run `corepack enable` if `pnpm` is unavailable.
- Prefer async file watchers (e.g. `watchfiles`) over manual polling in long-running automations.
- Keep configuration under version control and update `README.md` plus `.env.example` (when relevant) whenever new settings are introduced.
- Python tooling is standardised on Ruff; run `python -m ruff check` (and `python -m ruff format` when formatting changes are required) for any Python edits.
- Large knowledge artefacts belong under `data/knowledge/` and should stay out of commits unless explicitly required for tests.
- Before editing a component, inspect its directory for additional `AGENTS.md` files whose guidance takes precedence within that scope.

## Pull Request Expectations

1. Run the programmatic checks listed in the "Codex Meta-Intelligence" section when that project is modified; add any project-specific checks for other packages that you touch.
2. Update documentation whenever behaviour, configuration, or developer ergonomics change.
3. Keep commits focused and avoid committing generated artefacts, build outputs, or vendored dependencies.

## Codex Meta-Intelligence (`codex-meta-intelligence/`)

This workspace member is stage-managed via `stage.json` and `build.sh`. Treat the project root (`codex-meta-intelligence/`) as the execution context for stage automation.

### Environment Setup

- Install dependencies with `pnpm install --filter codex-meta-intelligence...`. Run the command from the repository root so pnpm resolves the workspace manifest correctly.
- Node.js 18+ and pnpm 8+ are required. Enable pnpm via `corepack enable` if necessary.
- Python dependencies are not needed for Stage 1; install them only when corresponding tests are added.

### Build & Stage Orchestration

- Execute `./codex-meta-intelligence/build.sh` from the repository root. The script dispatches tasks based on the current stage recorded in `codex-meta-intelligence/stage.json`.
- Never hand-edit `stage.json` unless you are repairing a failed promotion. The build script is responsible for advancing the stage and stamping completion metadata.
- When stage progression occurs, mention it explicitly in your PR summary.

### Quality Gates

Run the following commands from the repository root after making changes to this project:

- `pnpm --filter codex-meta-intelligence lint`
- `pnpm --filter codex-meta-intelligence test`
- `pnpm --filter codex-meta-intelligence typecheck`
- `pnpm --filter codex-meta-intelligence build`

If the build script introduces additional automated checks, re-run them locally to validate idempotency.

### Coding Standards

- Prefer named exports throughout TypeScript modules; avoid default exports.
- Embrace immutability and pure functions; when classes are necessary, expose explicit interfaces from `codex-meta-intelligence/src/shared/types.ts`.
- Keep files self-documented with clear comments, and do not leave TODO placeholders in committed code.
- Store Jest tests in `codex-meta-intelligence/tests/` and cover both success and failure scenarios.

### Logging & Telemetry

- Use the shared logger utilities in `codex-meta-intelligence/src/shared/utils.ts` to ensure consistent log structure.
- When adding metrics or traces, update both `codex-meta-intelligence/src/analytics/metrics.ts` and `codex-meta-intelligence/src/analytics/tracing.ts`.

## Cross-Project Notes

- Some packages (e.g. `backend/`, `apps/`, `packages/`) maintain their own tooling. Follow their local AGENTS or README instructions when modifying them.
- When integrating multiple packages in a single PR, document the relationship between changes so reviewers can understand the system impact.
