# Application Security Program

This repository follows a defense-in-depth security strategy that combines automated
static analysis, supply-chain checks, and targeted manual reviews. The goal is to
quickly surface high-impact issues while keeping remediation work focused and
manageable for the engineering team.

## Scanner Coverage

| Scanner                                  | When It Runs                                                              | Scope                                                                     | Output Location                                             |
| ---------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **CodeQL**                               | Weekly on `main`, every pull request, and on-demand via workflow dispatch | Full repository analysis for JavaScript/TypeScript and Python             | GitHub Security → Code Scanning Alerts                      |
| **Semgrep (incremental)**                | Every pull request                                                        | Only files changed in the PR compared against the base branch             | GitHub Security → Code Scanning Alerts + PR summary comment |
| **Snyk Code**                            | Weekly schedule when `SNYK_TOKEN` secret is configured                    | Full repository scan with proprietary rules                               | GitHub Security → Code Scanning Alerts                      |
| **Dependency, secret, and audit checks** | Every pull request + weekly schedule                                      | `pnpm audit`, `pip audit`, Bandit, dependency review, Husky pre-push gate | GitHub Actions log + PR annotations                         |
| **Gitleaks**                             | Weekly scheduled workflow + manual (`pnpm run scan:secrets`) invocations  | Full Git history using `scripts/scan-secrets.sh`                          | `results/security/gitleaks-report.*`                        |

### Scheduling Strategy

- **Full scans:** The `Full CodeQL Scan` and optional Snyk job run on a weekly cron to
  produce a comprehensive baseline and catch issues that incremental scans may miss.
- **Incremental scans:** The Semgrep job (`Incremental SAST`) triggers on each pull request
  and only analyzes the diff against the target branch, keeping feedback quick and relevant
  to the proposed changes.

## Common Vulnerability Classes

Developers should stay alert for the following issues when working in this codebase:

- **Injection flaws:** Command execution, SQL, and template injection risks can arise from
  unsanitized inputs. Always validate and encode user-controlled data before use.
- **Authentication & authorization:** Reuse the shared auth helpers and ensure every
  privileged action checks both identity and permissions. Avoid rolling your own tokens.
- **Insecure deserialization:** Avoid `eval`, `exec`, or `pickle` on untrusted data. Prefer
  safe parsers (e.g., `json.loads`) with schema validation.
- **Improper secrets handling:** Do not commit credentials or tokens. Use environment
  variables or secret managers. Automated secret scanning runs on each PR and you can perform
  manual sweeps with `pnpm run scan:secrets` before sharing high-risk branches.
- **Insecure defaults in configuration:** New configuration files should set secure defaults,
  enforce timeouts, and document how to override safely.

## Secure Coding Guidelines

- **Validate inputs at boundaries.** Use existing validation utilities and type hints to
  reject malformed data early.
- **Fail safely.** On errors, return clear messages without leaking stack traces or
  sensitive context. Ensure retries respect idempotency.
- **Use parameterized queries and prepared statements** for any database access.
- **Keep dependencies up to date** and prefer well-maintained libraries with active
  security advisories.
- **Limit third-party script execution** in front-end code and enable Content Security
  Policy (CSP) headers where applicable.
- **Log security-relevant events** (auth changes, privilege escalation, policy changes)
  using the shared logging utilities so anomalies can be audited.

## Working With Scanner Results

1. **Findings appear in GitHub Security → Code Scanning Alerts** or directly in the pull
   request checks. Expand each alert to see the rule description, location, and suggested fix.
2. **Prioritize remediation** using the following rubric:
   - `Critical`/`High` severity with low or medium remediation effort: fix immediately and
     block the release.
   - `High` severity with high effort: discuss with the security champion and schedule for the
     next sprint; apply compensating controls if available.
   - `Medium` severity: fix before merge when feasible. Otherwise, create a tracked ticket
     with owner and due date.
   - `Low` severity or informational: document the rationale for accepting the risk or fix when
     touching related code.
3. **Link commits or PRs** that resolve an alert to the finding so the code scanning dashboard
   stays accurate. Close stale alerts only after verifying the vulnerable code path no longer
   exists.

### Semgrep Incremental Scans

- Semgrep compares the current branch to the base branch using the `baseline-ref`
  configuration. Only new or modified findings are reported, which keeps PR feedback focused
  on changes introduced by the contributor.
- If a rule is noisy for a particular directory, tune it by adding suppressions to
  `.semgrepignore` or a rule-specific configuration. Coordinate adjustments with the security
  team.

### CodeQL and Snyk Full Scans

- Full scans may take longer and run asynchronously. Monitor the weekly workflow run for any
  regressions introduced since the last scan. Use the "Download SARIF" button to archive results in
  `results/security/` when deep dives are required.
- When the Snyk token is configured, results are uploaded as SARIF and surfaced in the same
  dashboard as CodeQL alerts for a unified triage experience.

### Interpreting CodeQL Findings

1. Expand the alert to review the call stack and data-flow trace. CodeQL highlights the
   "source" and "sink" to show how untrusted input reaches a dangerous API.
2. Cross-reference the impacted file with the relevant runbook in `docs/context/automation-pipeline.md`
   to determine remediation priority. Security issues inherit the SLA table published there.
3. If CodeQL suggests an automated fix, stage it in a dedicated branch and run
   `scripts/run-quality-gates.sh pre-push` before requesting review. Attach the SARIF snippet to the
   PR description so reviewers can verify the alert is resolved.
4. When suppressing a false positive, add a justification comment (`// codeql[rule-id]: reason`) and
   document the rationale in `results/ai-review/log.json` for audit purposes.

## Manual Review Checklist

Automated scanners cannot detect every issue, especially business-logic flaws. During code
review, engineers should:

- Verify that authorization logic aligns with product requirements (no privilege escalation or
  horizontal access issues).
- Confirm that financial or quota-related calculations enforce limits and handle rounding
  consistently.
- Review dangerous state transitions (e.g., workflow approvals, key rotations) for race
  conditions or missing audit trails.
- Ensure new third-party integrations meet compliance and privacy expectations.
- Document any accepted risk in the pull request description and create a follow-up ticket when
  remediation is deferred.

## Reporting Security Issues

If you discover a vulnerability, please follow the responsible disclosure practices outlined in
`SECURITY_CONTACT.md` (or contact the security team at security@example.com if running in an
enterprise environment). Do not open public issues that describe exploitable flaws until a fix
is available.

### Secret Scanning Playbook

Use `scripts/scan-secrets.sh [output_dir] [extra gitleaks args...]` to run ad-hoc scans. The helper
walks the entire Git history (`--log-opts="--all"`) and emits SARIF/JSON so alerts can be uploaded to
GitHub Security. Provide `--redact` for reports that omit secret contents when sharing outside the
security team.

Remediation workflow:

1. Immediately rotate the credential in the upstream system (cloud provider, SaaS integration, etc.).
2. Purge exposed values from Git history using `git filter-repo` or `git filter-branch` and force-push
   to invalidate cached clones. The `scripts/scan-secrets.sh` output lists file paths and commits to
   target.
3. Replace secrets with environment variables or managed secret stores. Update `.env.example` and
   related documentation to reflect the new variable name.
4. Record the incident in `results/security/remediation-log.md` (create if absent) with date,
   credential name, remediation owner, and follow-up tasks.
5. Re-run `scripts/run-quality-gates.sh pre-push` to ensure the leak has been eliminated before
   merging.
