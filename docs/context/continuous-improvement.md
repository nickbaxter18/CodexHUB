# Continuous Improvement & Metrics Playbook

_Last updated: 2024-09-27_

## Overview

CodexHUB tracks a set of operational metrics to make sure automated scans, build
pipelines, and manual reviews continue to deliver compounding benefits. This
playbook consolidates the signals emitted by the existing tooling and explains
how to extend them when new agents or services join the monorepo.

## Core Metrics

| Metric                                | Source                                           | Storage                                                  | Usage                                                                        |
| ------------------------------------- | ------------------------------------------------ | -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Build duration                        | `make quality` + GitHub Actions artifacts        | `results/performance/*.json`                             | Detect regressions in CI wall time and update Turbo task graph definitions.  |
| Lint/test failure rate                | Husky pre-commit logs, CI annotations            | GitHub Actions dashboard                                 | Highlight noisy rules that require suppression or refactoring.               |
| Secret scan findings                  | `scripts/scan-secrets.sh` SARIF, Gitleaks alerts | `results/security/gitleaks-report.sarif` + Code Scanning | Drive credential rotations and coverage of high-risk paths.                  |
| SAST findings (Semgrep, CodeQL, Snyk) | CI security workflows                            | GitHub Security tab                                      | Prioritise remediation with severity/effort rubric defined in `SECURITY.md`. |
| Agent compliance                      | `python scripts/auto_setup_cursor.py` telemetry  | `results/performance/cursor-status.json`                 | Ensure Cursor enforcement remains active for every automation task.          |

## Reporting Cadence

1. **Weekly security digest:** Triggered by the scheduled security workflow. Export
   SARIF summaries and circulate high/critical findings with proposed owners.
2. **Bi-weekly quality review:** Compare `results/performance/` timing deltas across
   the last four `make quality` runs. Update Turbo dependencies or caching strategy
   when durations climb >10% week-over-week.
3. **Monthly governance sync:** Refresh the knowledge bundle with
   `scripts/fetch-context.sh` and ensure docs in `docs/context/` reflect the latest
   architecture, policies, and playbooks.

## Extending the Pipeline

- **New packages:** Add their build/test tasks to `turbo.json` and extend the
  metrics table with package-specific telemetry targets.
- **Additional scanners:** Wire SARIF outputs through the same upload step used by
  CodeQL/Snyk/Gitleaks so findings land in the central dashboard.
- **Agent orchestration:** Record acceptance/rejection stats for AI-assist
  suggestions in `results/performance/cursor-status.json` to refine future review
  workflows. Update this document with any new data sources as they appear.

Keeping this playbook current gives both humans and automated agents a single
source of truth for measuring progress and planning the next iteration of
improvements.
