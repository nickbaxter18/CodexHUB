# Automated Scan–Diagnose–Fix Pipeline

_Last updated: 2024-12-04_

This blueprint describes how CodexHUB orchestrates automated scanning, diagnosis, remediation,
and knowledge capture so that quality signals feed directly into action plans.

## Pipeline Overview

```mermaid
flowchart TD
  A[Trigger (commit / schedule / manual)] --> B[Run Quality Gates]
  B --> C{Issues Found?}
  C -- No --> Z[Log success + update metrics]
  C -- Yes --> D[Classify Findings]
  D --> E[Generate remediation plan]
  E --> F[Propose patches]
  F --> G[Human/AI review]
  G --> H{Accepted?}
  H -- Yes --> I[Merge + run metrics script]
  H -- No --> J[Log rejection + escalate]
  I --> Z
  J --> Z
```

## Execution Steps

1. **Trigger** – Workflows run on PRs, pushes to `main`, scheduled jobs (`codeql.yml`, security sweeps), and manual invocations of `scripts/run-quality-gates.sh` from developer machines.
2. **Quality Gate Execution** – `scripts/run-quality-gates.sh <stage>` drives linting, testing, SAST, and secret scans. Each run streams telemetry to `scripts/metrics/record_quality_gate.py`, which appends JSON lines to `results/metrics/quality-gates-log.ndjson` and captures the latest snapshot in `results/metrics/quality-gates-latest.json`.
3. **Classification** – Findings feed into `results/security/` (SARIF) and `results/metrics/`. Use severity tags from CodeQL/Semgrep and map secrets via `scripts/scan-secrets.sh` output.
4. **Remediation Planning** – Create issue templates (see `.github/ISSUE_TEMPLATE/`) describing scope, severity, and proposed owner. Update `docs/context/ai-assisted-review.md` when AI-generated fixes are requested.
5. **Patch Generation** – Prefer automated patches via Semgrep autofix, Cursor agents, or typed codemods. Attach context bundle archives for reviewer parity.
6. **Review & Merge** – Follow the AI-assisted review playbook. Log accepted/rejected suggestions with `scripts/metrics/log_ai_review.py` and update metrics via `scripts/metrics/collect_metrics.py --skip-commands` if rerunning builds is unnecessary.
7. **Learning Log** – Append summary entries to `results/improvements/log.md` (create if absent) and link back to the relevant quality-gate record so retrospectives can correlate outcomes with the execution timeline.

## Categorisation Heuristics

| Category   | Criteria                            | Default Owner     | Remediation SLA |
| ---------- | ----------------------------------- | ----------------- | --------------- |
| Security   | CodeQL/semgrep High+, Gitleaks hits | Security champion | 48 hours        |
| Quality    | Test or lint failures               | Module maintainer | 72 hours        |
| Governance | Policy drift, missing docs          | Docs lead         | 7 days          |

## Automation Hooks

- Extend `.github/workflows/security-pr.yml` to upload SARIF from any new scanner.
- Use `scripts/metrics/collect_metrics.py` in scheduled mode to create weekly dashboards.
- Capture developer-side telemetry by invoking `scripts/run-quality-gates.sh pre-push`, which automatically records outcomes via `results/metrics/quality-gates-log.ndjson`.
- Publish remediation patches via `results/automation/remediations/<date>.md` for traceability.

Keeping this loop documented ensures all agents know how to translate findings into fixes without
waiting for manual coordination.
