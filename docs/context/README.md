# Context Hub

The Context Hub centralises the architectural knowledge required for automated and human
contributors to operate effectively inside CodexHUB. It aggregates domain guidelines,
reusable component catalogs, and operational runbooks in a predictable directory so that
context can be fetched programmatically via `scripts/fetch-context.sh` or browsed manually by
engineers. Every document in this folder should remain concise, link back to authoritative
sources when available, and highlight how to apply the guidance in day-to-day development.

## Directory Map

| File                 | Description                                                               |
| -------------------- | ------------------------------------------------------------------------- |
| `design-patterns.md` | Canonical implementation patterns and anti-patterns for the codebase.     |
| `best-practices.md`  | Consolidated coding, testing, security, and operational practices.        |
| `api-schemas.md`     | High-level view of public APIs, shared data models, and validation flows. |
| `getting-started.md` | Quick-start instructions for local setup, builds, and deployments.        |
| `knowledge-graph.md` | Machine-readable summary of major subsystems and their dependencies.      |

### Maintenance Rules

- Update this index whenever a new context document is added.
- Keep cross-links to existing docs (`ARCHITECTURE.md`, `SECURITY.md`, etc.) accurate so the
  fetch script can package canonical references.
- Note the version or date of last revision at the top of long-lived documents to help agents
  decide when to refresh their cached knowledge.
