# Repository Audit — 2025-09-27

_Last updated: 2025-09-27T00:00:00Z_

## Knowledge Graph Enhancements
- Snapshot generator now inventories governance artefacts (`AGENT.md` / `AGENTS.md`) and key lint/build configuration alongside nodes and edges.
- Markdown digest extended with "Governance Artifacts" and "Quality Configuration Files" tables for rapid compliance assessment.
- Regenerated snapshot at 2025-09-27T00:00Z capturing three governance directives and nineteen quality configuration files.

## Issue Catalogue
| Category | Priority | Finding | Evidence | Recommendation |
| --- | --- | --- | --- | --- |
| Compliance | High | Governance scope was previously scattered across Markdown files without a consolidated index. | Lack of governance coverage section in `results/metrics/repo-graph-summary.md` before 2025-09-27. | Extend the snapshot generator to emit governance and tooling inventories for every run. |
| Tooling | Medium | Quality gate configs were difficult to audit due to manual tree inspection. | Pre-update audit logs and missing summary tables. | Include config discovery in the snapshot digest and keep the context fetcher bundling the enriched artefacts. |

## Proposed Fixes & Effort
- **Governance discovery:** Moderate Python update (~20 min) to walk the workspace safely without entering caches and append artefact metadata to the knowledge graph JSON.
- **Digest expansion:** Lightweight Markdown generation extension (~5 min) to present the new data in tabular form for auditors.

## Changes Applied Automatically
- Updated `scripts/metrics/generate_repo_snapshot.py` to crawl governance directives and quality configuration files while respecting skip lists for cache directories.
- Regenerated `results/metrics/repo-graph.{json,mmd}` and refreshed the Markdown digest to surface the new sections.
- Documented the discovery workflow in `docs/context/knowledge-graph.md` and recorded this cycle in the improvement log.

## Pending Tasks & Next Actions
1. Teach the snapshot generator to categorise CI workflow definitions (`.github/workflows/`) once the repository standardises on a pipeline set.
2. Pipe the governance/config inventory into CI artefacts or dashboards so compliance reviewers can diff runs across time.
3. Expand skip lists and classification rules as new package types or tooling manifests are added to the workspace.
