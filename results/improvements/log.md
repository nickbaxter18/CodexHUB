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
