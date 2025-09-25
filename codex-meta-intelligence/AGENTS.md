# Codex Meta-Intelligence Project Instructions

## Environment Setup

- Use **pnpm** for JavaScript and TypeScript dependency management inside this project (`pnpm install --ignore-workspace-root-check`).
- Node.js 18+ and pnpm 8+ are required. Use `corepack enable` if pnpm is unavailable.
- Install Python dependencies only when tests reference them; the Stage 1 stack runs entirely on Node.js/TypeScript.

## Build & Stage Orchestration

- The `build.sh` script governs all automated actions. Run it from the project root (`./build.sh`).
- `stage.json` tracks the active stage. Do not edit it manually unless recovering from a failed build.

## Testing & Quality Gates

- Run `pnpm lint` for ESLint/Prettier checks and `pnpm test` for Jest unit tests before committing.
- Execute `pnpm typecheck` to ensure TypeScript passes strict compilation.
- Stage scripts may execute these commands automatically; rerun them locally when modifying logic.

## Coding Standards

- TypeScript code must use named exports where possible and avoid default exports.
- Favor immutability and pure functions. Classes should expose explicit interfaces from `src/shared/types.ts`.
- Keep files self-documented with descriptive comments and avoid TODO placeholders.
- Tests belong under `tests/` and should verify both success and failure paths.

## Logging & Telemetry

- Use the shared logger utilities in `src/shared/utils.ts` for consistent logging.
- When adding new metrics or traces, update `src/analytics/metrics.ts` and `src/analytics/tracing.ts`.

## Pull Request Guidelines

- Summaries must mention stage progression when `stage.json` changes.
- Include references to relevant documentation markdown files when adding new capabilities.
- Ensure CI scripts and build orchestrations remain idempotent and safe to re-run.
