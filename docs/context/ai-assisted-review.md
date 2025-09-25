# AI-Assisted Review Playbook

_Last updated: 2024-12-04_

CodexHUB relies on automated reasoning agents to accelerate code review while preserving
human oversight. This playbook codifies how to configure tools, interpret their
suggestions, and record decisions so that the workflow remains auditable.

## Tooling Configuration

| Layer               | Tool / Integration                          | Configuration Notes                                                                                 |
| ------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Static analysis     | CodeQL (CI), Semgrep (pre-commit & CI)      | Ensure queries listed in `.github/workflows/codeql.yml` and `.pre-commit-config.yaml` stay in sync. |
| Dependency scanning | `pip-audit`, `pnpm audit`, Renovate bots    | Record baseline results in `results/security/` and create issues for new advisories.                |
| AI review assistant | Cursor agents + Meta-Agent reviewer         | Enforce via `scripts/run-quality-gates.sh` and `src/cursor` compliance utilities.                   |
| Knowledge surfacing | `scripts/fetch-context.sh --archive` bundle | Attach generated archive to PRs so reviewers share identical context.                               |

## Review Workflow

1. **Kick-off** – Agents generate proposals referencing context bundle manifests.
2. **Automated vetting** – Husky pre-push gate runs full lint/test suites, gitleaks, and
   Semgrep to weed out obvious regressions.
3. **AI suggestion capture** – Store AI-authored diffs in `results/ai-review/` (one file per
   proposal) with metadata: originating agent, prompt summary, decision state.
4. **Human arbitration** – Maintainers review AI suggestions alongside CodeQL/Semgrep
   findings. Approval thresholds:
   - ✅ _Auto-merge candidates_ must pass all quality gates and earn at least one
     maintainer approval.
   - ⚠️ _Conditional candidates_ require manual edits or additional tests before merge.
   - ❌ _Rejected candidates_ should be annotated with reason codes (accuracy, security,
     style) for analytics.
5. **Decision logging** – Update `results/ai-review/log.json` with entries containing:
   commit SHA, accepted suggestion IDs, rejected suggestion IDs, reviewer, and rationale.

## Metrics & Continuous Feedback

- **Acceptance rate** – Ratio of accepted vs. total AI suggestions per release cycle.
- **Time-to-merge delta** – Compare PR cycle times for AI-assisted vs. manual patches.
- **Escalations** – Track instances where AI changes triggered incident responses or
  post-merge rollbacks.

Feed these metrics into `scripts/metrics/collect_metrics.py` via custom command groups and
extend the history file when new signals become important. Reflect updates in
`docs/context/continuous-improvement.md` so the entire review pipeline remains transparent.
