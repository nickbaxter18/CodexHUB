# Repository Audit — 2025-09-25

_Last updated: 2025-09-25T21:03:00Z_

## Knowledge Graph Summary
- Regenerated `results/metrics/repo-graph.json` and Mermaid artefacts via `python scripts/metrics/generate_repo_snapshot.py` after filtering out cached workspace members (`__pycache__`).
- Active workspace nodes: `agents/`, `apps/editor`, `codex-meta-intelligence`, `macro_system`, `meta_agent`, `packages/automation`, `qa_engine`, `rentalos-ai`, `scripts/`, and the Cursor/Knowledge/Mobile integrations under `src/`.
- Dense import edges continue to originate from `packages/automation` into `macro_system` and `meta_agent`, while `scripts/` depends heavily on `src/` utilities; no new cross-package imports were detected in this pass.

## Issue Catalogue
| Category | Priority | Finding | Evidence | Recommendation |
| --- | --- | --- | --- | --- |
| Security | High | Unable to complete `pnpm run scan:secrets` because gitleaks/Docker are unavailable in the execution environment. | CLI failure at 2025-09-25T21:02Z. | Provision gitleaks locally or enable Docker so the scan can run; schedule a rerun and archive SARIF/JSON outputs. |
| Quality | Low | Knowledge graph previously included `packages/__pycache__`, inflating node count with transient artefacts. | Historical Mermaid snapshot (`results/metrics/repo-graph.mmd`) before filter patch. | Patched generator to ignore cache directories; confirm downstream consumers refresh their bundles. |

## Proposed Fixes & Effort
- **Security:** Installing gitleaks (`brew install gitleaks` or GitHub release binary) or enabling Docker is a small effort (<30 min) but must occur on developer machines/CI runners with elevated permissions. Follow-up run should be captured in `results/security/`.
- **Knowledge Graph Hygiene:** Already implemented via script patch; negligible ongoing effort beyond ensuring bundlers pull the latest metrics.

## Changes Applied Automatically
- Updated `scripts/metrics/generate_repo_snapshot.py` to skip cache directories.
- Regenerated knowledge graph artefacts in `results/metrics/`.
- Documented the cache filter addition in `docs/context/knowledge-graph.md` and logged the audit in `results/improvements/log.md`.

## Pending Tasks & Next Actions
1. Restore secret scanning coverage by installing gitleaks or enabling Docker, then rerun `pnpm run scan:secrets -- --report-format sarif` and upload results to the security dashboard.
2. Circulate refreshed knowledge graph artefacts via `scripts/fetch-context.sh --archive` so reviewers receive the updated bundle.
3. During the next governance sync, verify that CI agents inherit the cache-filtered graph and incorporate the change into any downstream dashboards.
