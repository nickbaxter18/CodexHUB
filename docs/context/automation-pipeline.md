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

1. **Trigger** – Workflows run on PRs, pushes to `main`, and scheduled jobs (`codeql.yml`,
   `scheduled_security.yml`). Manual execution is available via `scripts/run-quality-gates.sh` or
   `scripts/metrics/collect_metrics.py --run-commands`.
2. **Quality Gates** – Husky pre-push hook (and CI) execute lint, format, pnpm/PyTest suites,
   Cursor validation, Semgrep SAST, and Gitleaks history scans.
3. **Classification** – Findings feed into `results/security/` (SARIF) and `results/metrics/`. Use
   severity tags from CodeQL/Semgrep and map secrets via `scripts/scan-secrets.sh` output.
4. **Remediation Planning** – Create issue templates (see `.github/ISSUE_TEMPLATE/`) describing
   scope, severity, and proposed owner. Update `docs/context/ai-assisted-review.md` when AI-generated
   fixes are requested.
5. **Patch Generation** – Prefer automated patches via Semgrep autofix, Cursor agents, or
   typed codemods. Attach context bundle archives for reviewer parity.
6. **Review & Merge** – Follow AI-assisted review playbook. Log accepted/rejected suggestions and
   update metrics via `scripts/metrics/collect_metrics.py --skip-commands` if rerunning builds is
   unnecessary.
7. **Learning Log** – Append summary entries to `results/improvements/log.md` (create if absent)
   capturing root cause, fix lead time, and follow-up actions. Reference this log in retrospectives.

## Categorisation Heuristics

| Category   | Criteria                            | Default Owner     | Remediation SLA |
| ---------- | ----------------------------------- | ----------------- | --------------- |
| Security   | CodeQL/semgrep High+, Gitleaks hits | Security champion | 48 hours        |
| Quality    | Test or lint failures               | Module maintainer | 72 hours        |
| Governance | Policy drift, missing docs          | Docs lead         | 7 days          |

## Automation Hooks

- Extend `.github/workflows/security-pr.yml` to upload SARIF from any new scanner.
- Use `scripts/metrics/collect_metrics.py` in scheduled mode to create weekly dashboards.
- Publish remediation patches via `results/automation/remediations/<date>.md` for traceability.

Keeping this loop documented ensures all agents know how to translate findings into fixes without
waiting for manual coordination.
