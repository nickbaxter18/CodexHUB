# Context Hub

The Context Hub centralises the architectural knowledge required for automated and human
contributors to operate effectively inside CodexHUB. It aggregates domain guidelines,
reusable component catalogs, and operational runbooks in a predictable directory so that
context can be fetched programmatically via `scripts/fetch-context.sh` or browsed manually by
engineers. Every document in this folder should remain concise, link back to authoritative
sources when available, and highlight how to apply the guidance in day-to-day development.

## Directory Map

| File                           | Description                                                                |
| ------------------------------ | -------------------------------------------------------------------------- |
| `design-patterns.md`           | Canonical implementation patterns, reusable components, and anti-patterns. |
| `best-practices.md`            | Consolidated coding, testing, security, and operational practices.         |
| `api-schemas.md`               | High-level view of public APIs, shared data models, and validation flows.  |
| `getting-started.md`           | Quick-start onboarding instructions for local setup and CI parity.         |
| `knowledge-graph.md`           | Machine-readable summary of major subsystems and their dependencies.       |
| `continuous-improvement.md`    | Metrics, reporting cadence, and guidance for sustaining repo health.       |
| `automation-pipeline.md`       | End-to-end scan→diagnose→fix orchestration blueprint.                      |
| `ai-assisted-review.md`        | Procedures for configuring AI reviewers and logging decision outcomes.     |
| `monorepo-strategy.md`         | Evaluation of Turbo/Nx/Bazel adoption paths and workspace segmentation.    |
| `multi-agent-orchestration.md` | Future-state coordination model across knowledge, scanning, and QA roles.  |

### Maintenance Rules

- Update this index whenever a new context document is added.
- Keep cross-links to existing docs (`ARCHITECTURE.md`, `SECURITY.md`, etc.) accurate so the
  fetch script can package canonical references.
- Note the version or date of last revision at the top of long-lived documents to help agents
  decide when to refresh their cached knowledge.
- Regenerate the bundle with `scripts/fetch-context.sh --archive` after substantial updates so
  automated reviewers consume the latest knowledge pack.
