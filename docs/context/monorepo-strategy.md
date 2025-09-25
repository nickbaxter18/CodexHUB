# Monorepo Strategy Evaluation

_Last updated: 2024-12-04_

CodexHUB already operates as a polyglot monorepo containing JavaScript/TypeScript, Python, and
infrastructure assets. This document records the evaluation of formalising the structure around
`apps/`, `packages/`, and shared libraries, and it recommends tooling for incremental builds.

## Current State Assessment

- **Workspace layout** – `pnpm-workspace.yaml` defines packages under `apps/*`, `packages/*`, and
  custom directories such as `codex-meta-intelligence` and `backend`. Dependencies are largely
  managed via pnpm workspace protocols.
- **Build orchestration** – Turbo (`turbo.json`) runs lint/test/build across packages, but not all
  subprojects declare explicit pipelines.
- **Caching** – CI leverages pnpm cache + Turbo remote caching (optional), yet Python tooling runs
  outside the graph.

## Recommended Enhancements

1. **Adopt Turbo pipeline consistently**
   - Add each package's lint/test/build commands to `turbo.json`.
   - Use `dependsOn` to chain shared libraries before app builds.
   - Enable remote caching (e.g., Vercel Remote Cache or self-hosted Redis) for CI parity.
2. **Library segregation**
   - Move cross-cutting utilities under `packages/lib-*` to avoid duplicate imports from `src/`.
   - Publish shared TypeScript types from `packages/types` and Python utilities from
     `packages/python-tools` to align namespacing.
3. **Incremental Python builds**
   - Introduce `uv` or `pixi` for Python dependency graphs and integrate with Turbo via custom
     tasks that call `poetry`/`uv run` commands.
   - Cache `.venv` or `.uv` directories per package using GitHub Actions cache keys.
4. **Bazel feasibility**
   - Bazel would provide hermetic builds but requires significant migration. Re-evaluate once
     Turbo coverage hits 90% of packages and cross-language builds become a bottleneck.

## Decision Framework

| Option | Pros                                         | Cons                                    | Next Action                                                                     |
| ------ | -------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------- |
| Turbo  | First-class pnpm support, lightweight config | Limited Python ecosystem integrations   | Expand task graph, integrate metrics from `scripts/metrics/collect_metrics.py`. |
| Nx     | Strong plugin ecosystem, visual dep graph    | Requires migration from Turbo tasks     | Prototype Nx executor for one package if Turbo gaps persist.                    |
| Bazel  | Hermetic, reproducible builds                | Steep learning curve, new tooling stack | Defer until infra team commits to dedicated maintenance.                        |

## Implementation Roadmap

1. Document Turbo task ownership in `docs/context/best-practices.md`.
2. Add Python build/test proxies under `packages/python-tools/` and wire them into Turbo.
3. Revisit evaluation quarterly and update this file with measured build/test durations sourced
   from `results/metrics/history.json`.
