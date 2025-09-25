# Improvement Log

Use this ledger to capture lessons learned from automated scans and remediation efforts.
Document:

- Date
- Trigger (scan, incident, retrospective)
- Summary of findings
- Remediation steps
- Follow-up tasks / owners

## 2025-09-25 — Quality gate telemetry instrumentation

- **Trigger:** Deep-dive automation audit approving expansion of metrics capture.
- **Summary:** Added `scripts/metrics/record_quality_gate.py` and wired
  `scripts/run-quality-gates.sh` to emit NDJSON snapshots plus a latest summary for
  every stage invocation.
- **Remediation steps:** Generated the first repository graph snapshot, created the
  AI review ledger via `scripts/metrics/log_ai_review.py`, and documented the
  workflow across `docs/context/knowledge-graph.md`,
  `docs/context/continuous-improvement.md`, and
  `docs/context/automation-pipeline.md`.
- **Follow-up:** Monitor the new ledger during the next scheduled governance sync
  and expand coverage to package-specific gates once Python projects gain
  dedicated Turbo tasks.

## 2025-09-25 — Repository audit refresh

- **Trigger:** Follow-up repository improvement cycle initiated after user approval.
- **Summary:** Regenerated the workspace knowledge graph, removed `__pycache__`
  artefacts from the snapshot generator, and reviewed secret scanning coverage.
- **Remediation steps:** Patched `scripts/metrics/generate_repo_snapshot.py` to
  exclude cache directories, refreshed `results/metrics/repo-graph.*`, and
  documented the cache filter in `docs/context/knowledge-graph.md`.
- **Follow-up:** Install gitleaks or enable Docker in the execution environment so
  `pnpm run scan:secrets` can complete; schedule the run after environment support
  improves and archive the resulting SARIF/JSON outputs in `results/security/`.

## 2025-09-26 — Knowledge graph digest automation

- **Trigger:** Approved repository-improvement follow-up to extend context bundles.
- **Summary:** Added a Markdown digest export to the snapshot generator so audits
  can surface node counts, dependency hotspots, and workspace membership without
  parsing JSON artefacts.
- **Remediation steps:** Updated `scripts/metrics/generate_repo_snapshot.py` to
  produce `repo-graph-summary.md`, refreshed the metrics bundle, expanded
  `scripts/fetch-context.sh` coverage, and documented the workflow in
  `docs/context/knowledge-graph.md`.
- **Follow-up:** Wire the summary output into CI artefact uploads once the
  pipeline has storage for Markdown reports, and investigate enriching the digest
  with CodeQL/SAST findings when those scanners land.

## 2025-09-27 — Governance inventory capture

- **Trigger:** Continuous-improvement directive to expose AGENT/AGENTS scope and
  configuration coverage through the knowledge graph artefacts.
- **Summary:** Extended the snapshot generator to crawl governance directives and
  quality gate manifests, adding tabular views to the Markdown digest for rapid
  compliance review.
- **Remediation steps:** Implemented repository-safe traversal with skip lists,
  regenerated the metrics bundle, updated the knowledge graph guide, and issued a
  dated audit report summarising the new inventory.
- **Follow-up:** Integrate CI workflow discovery in a future cycle and publish
  the governance/config manifest as part of routine context bundles and audit
  dashboards.
