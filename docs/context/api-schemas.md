# API Schemas & Data Models

_Last updated: 2024-12-04_

## HTTP Services

| Service           | Path         | Description                                                | Schema Source                              |
| ----------------- | ------------ | ---------------------------------------------------------- | ------------------------------------------ |
| Codex CLI backend | `/healthz`   | Liveness check used by orchestrators.                      | `backend/src/middleware/health-check.ts`   |
| Codex bridge      | `/api/plans` | Validates and stores plan definitions submitted by agents. | `codexbridge/src/schemas/plan.schema.json` |
| Editor service    | `/api/auth`  | Issues ephemeral tokens for the Codex Editor front-end.    | `apps/editor/pages/api/auth.ts`            |

All HTTP payloads should be validated through AJV schemas defined under
`packages/automation/src/validation` or JSON Schema artifacts in `codexbridge/src/schemas/`.
When adding new endpoints, generate a schema via `pnpm run generate:schema` (see `package.json`
for the TypeScript JSON schema script) and document it here.

## Shared Data Models

| Domain                    | File(s) / Schema                                  | Notes                                                                                                      |
| ------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Agent Capability Registry | `codex-meta-intelligence/src/registry/*.ts`       | Each capability exports a `CapabilityDefinition`; mirror updates in `docs/context/knowledge-graph.md`.     |
| Macro Definitions         | `macro_system/definitions/*.yml`                  | Validate via `python -m yamllint` and ensure inputs/outputs are documented alongside automation pipelines. |
| QA Checklists             | `qa_engine/checklists/**/*.md`                    | Keep headings standard (`## Preconditions`, `## Steps`, `## Verification`) so context bundler can parse.   |
| Security Policies         | `SECURITY.md`, `.github/workflows/security-*.yml` | Record remediation SLAs and scanner configurations to keep automation-pipeline heuristics accurate.        |

## Validation & Tooling

- Run `pnpm run validate:configs` (defined in `scripts/validate_configs.py`) after editing schemas to
  ensure the JSON files remain consistent.
- Use Zod or TypeScript interfaces when bridging typed and untyped layers. Record shared types in
  `packages/automation/src/types.ts` and update the knowledge graph accordingly.
- Capture schema revisions in `results/metrics/latest.json` by rerunning
  `scripts/metrics/collect_metrics.py --skip-commands` so downstream tooling notices version shifts.
