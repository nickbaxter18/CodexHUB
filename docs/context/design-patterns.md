# Design Patterns & Anti-Patterns

_Last updated: 2024-11-23_

## Preferred Architectural Patterns

- **Evented micro-frontends for editors (`apps/editor/`)**: Use Next.js routing with explicit
  module boundaries. Components should consume shared utilities via workspace imports rather
  than relative deep-links to keep the dependency graph observable by Turbo.
- **Agent capability encapsulation (`codex-meta-intelligence/`)**: Package each capability as a
  pure TypeScript module exporting factories through `src/shared/types.ts`. Prefer composition
  over inheritance and enforce immutability where possible.
- **Automation workflows (`packages/automation/`)**: Model long-running flows as state machines
  persisted via JSON schemas defined in `packages/automation/schemas/`. Each transition must be
  idempotent and implement a retry/backoff policy.
- **Python utilities (`agents/`, `qa/`)**: Follow functional programming conventions and keep
  side-effects behind small adapter functions. Use the shared logging helpers in
  `qa_engine/common/logging.py` for consistent observability.

## Reusable Components

| Component           | Location                                      | Notes                                                                                            |
| ------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Logger utility      | `codex-meta-intelligence/src/shared/utils.ts` | Emits structured logs with correlation IDs; import instead of `console.log`.                     |
| Schema validation   | `packages/automation/src/validation`          | Builds AJV validators for JSON payloads; update central schema when adding properties.           |
| Cursor bootstrap    | `scripts/auto_setup_cursor.py`                | Kickstarts IDE integration and compliance enforcement.                                           |
| Mobile app controls | `src/mobile`                                  | Provides async interfaces for remote goal management; reuse rather than duplicating API clients. |

## Anti-Patterns To Avoid

- **Implicit context coupling**: Do not rely on hard-coded relative paths between apps and
  packages. Use workspace aliases defined in `tsconfig.json` or convert to shared libraries.
- **Unchecked async operations**: Always await Promises and capture errors through the shared
  telemetry utilities; avoid fire-and-forget tasks unless intentionally queued.
- **Duplicated secret-handling logic**: Centralise secret resolution via the helper functions in
  `config/secrets.ts` to keep auditing manageable.
- **Copying build scripts**: Extend the Turbo pipeline or `Makefile` tasks instead of creating
  ad-hoc shell scripts that drift from the canonical workflow.

## Extension Guidelines

When introducing new modules, document them here and update the knowledge graph so future
contributors and automated agents can discover the new capabilities automatically.
