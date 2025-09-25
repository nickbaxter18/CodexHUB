# Multi-Agent Orchestration Blueprint

_Last updated: 2024-12-04_

The CodexHUB roadmap includes a coordinated mesh of agents specialising in knowledge
curation, scanning, planning, execution, and QA. This blueprint documents the intended
roles and hand-offs so we can activate the model once foundational controls are stable.

## Agent Roles

| Role              | Responsibilities                                                    | Key Inputs                                   | Deliverables                                |
| ----------------- | ------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------- |
| Knowledge Curator | Maintain docs/context hub, refresh context bundles, tag updates     | `docs/context/*`, `scripts/fetch-context.sh` | Updated manifests, change summaries         |
| Scanner           | Execute security & quality gates (Husky, CodeQL, Semgrep, Gitleaks) | CI workflows, `scripts/run-quality-gates.sh` | Findings feed (`results/security/`, alerts) |
| Planner           | Translate findings into actionable plans                            | Scanner outputs, `SECURITY.md`, `ROADMAP.md` | Issue templates, remediation playbooks      |
| Executor          | Apply fixes, run tests, request reviews                             | Plans, context bundle                        | PRs, patch sets, updated metrics            |
| QA Verifier       | Validate behaviour/regressions, track AI suggestion outcomes        | Test suites, `results/ai-review/` logs       | Sign-off reports, release notes             |

## Coordination Model

1. **Context Sync** – Knowledge curator publishes a fresh archive via
   `scripts/fetch-context.sh --archive` on a weekly cadence.
2. **Scan Cycle** – Scanner agent triggers `scripts/run-quality-gates.sh pre-push` (or CI) and
   records findings. CodeQL scheduled workflow provides deep scans every Sunday.
3. **Planning Session** – Planner agent analyses findings, prioritises based on SLA table in
   `docs/context/automation-pipeline.md`, and drafts remediation issues.
4. **Execution Sprint** – Executor agent claims issues, leverages Cursor integrations, and submits
   PRs referencing the plan ID.
5. **QA Review** – QA verifier runs targeted tests, updates AI review logs, and either approves or
   reopens the work.
6. **Retrospective Loop** – Metrics from `results/metrics/latest.json` feed into governance reviews.

## Activation Checklist

- [ ] Establish ownership roster for each role with escalation contacts.
- [ ] Automate context archive upload as part of weekly governance meetings.
- [ ] Integrate planner/executor coordination via GitHub Projects or Linear.
- [ ] Build dashboards from metrics history to surface SLA breaches automatically.

Once these boxes are checked, enable continuous operation by wiring each agent trigger into CI/CD
or ChatOps commands so that manual intervention becomes the exception rather than the rule.
