# Knowledge Graph Snapshot

_Last updated: 2025-09-25_

The repository graph is generated automatically by `scripts/metrics/generate_repo_snapshot.py` and
stored in `results/metrics/repo-graph.json` (JSON) and
`results/metrics/repo-graph.mmd` (Mermaid). Re-run the script whenever packages or
services move so the visualisation and downstream tooling remain consistent.

```mermaid
graph TD
  agents[agents]
  apps_editor[agents.md]
  codex-meta-intelligence[codex-meta-intelligence]
  macro_system[macro_system]
  meta_agent[meta_agent]
  packages_automation[automation]
  qa_engine[qa_engine]
  rentalos-ai[rentalos-ai]
  scripts[scripts]
  src[src]
  src_cursor[@codexhub/cursor-integration]
  src_knowledge[@codexhub/knowledge-integration]
  src_mobile[@codexhub/mobile-integration]
  src -->|imports| agents
  packages_automation -->|imports(9)| macro_system
  packages_automation -->|imports| agents
  packages_automation -->|imports(13)| meta_agent
  scripts -->|imports(27)| src
  scripts -->|imports| agents
  agents -->|imports(6)| packages_automation
```

## Node Summaries

- **`src`** – Core orchestration layer that wires CLI flows to Cursor, knowledge, mobile, and
  automation components. Heavy Python cross-imports originate here, so structural refactors should
  update this node first.
- **`packages/automation` (`automation`)** – Shared agent workflow engines that power macro,
  meta-agent, and QA automation; note the dense import edges into `macro_system` and `meta_agent`.
- **`scripts/`** – Operational tooling (quality gates, setup automation) that extends core services;
  most scripts import from `src` to enforce policy during developer workflows.
- **`agents/`** – Prompt libraries and governance assets consumed both by automation packages and
  runtime services.
- **`apps/editor`** – Next.js front-end for documentation/editorial workflows. Currently independent
  of the Python graph but still part of the workspace inventory.
- **`codex-meta-intelligence`** – TypeScript workspace for the meta-intelligence runtime; integrates
  with automation libraries rather than Python modules.
- **`macro_system`, `meta_agent`, `qa_engine`** – Python subsystems supplying macros, planning, and QA
  execution. Import edges highlight their reliance on `packages/automation` abstractions.
- **`src/cursor`, `src/knowledge`, `src/mobile`** – Cursor enforcement, knowledge ingestion, and
  mobile control services that participate in the workspace but currently have no direct import edges
  from other Python packages; they are invoked dynamically via runtime entrypoints.
- **`rentalos-ai`** – Standalone workspace entry for rental OS integrations.

## Edge Semantics

- **Imports** – Directed edges represent Python import relationships discovered via AST-free regex
  scanning. High counts (e.g., `imports(27)`) indicate hotspots worth watching during refactors.
- **Workspace Inventory** – Nodes without edges (e.g., `apps/editor`) are still tracked so the
  context bundle stays authoritative even when code is loosely coupled.
- **Regeneration Workflow** – The snapshot script respects pnpm workspace definitions and the Python
  roots declared in `pyproject.toml`. When adding a new package, update the workspace config then run
  `python scripts/metrics/generate_repo_snapshot.py` to refresh this document and the metrics bundle.
