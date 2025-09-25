# API Schemas & Data Models

_Last updated: 2024-11-23_

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

- **Agent Capability Registry (`codex-meta-intelligence/src/registry`)**: Each capability exports a
  `CapabilityDefinition` typed via `src/shared/types.ts`. Update the registry index when adding new
  capabilities and ensure the knowledge graph references the new node.
- **Macro Definitions (`macro_system/definitions`)**: YAML-based macros parsed via
  `macro_system/src/loader.ts`. Validate with `yamllint` and document preconditions/outputs in this
  file to keep the automation catalog synchronised.
- **QA Checklists (`qa_engine/checklists`)**: Markdown checklists consumed by the QA engine. Use
  consistent headings so the context fetch script can parse them.

## Validation & Tooling

- Run `pnpm run validate:configs` (defined in `scripts/validate_configs.py`) after editing schemas to
  ensure the JSON files remain consistent.
- Use Zod or TypeScript interfaces when bridging typed and untyped layers. Record shared types in
  `packages/automation/src/types.ts` and update the knowledge graph accordingly.
