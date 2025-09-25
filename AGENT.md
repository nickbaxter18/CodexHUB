# CodexHUB Agent Architecture Overview

The CodexHUB workspace hosts several autonomous and semi-autonomous agent systems. This document centralises the high-level orientation material for every agent-facing capability so that contributors can locate the authoritative specifications without hunting through individual subprojects. The content now mirrors the Codex Meta-Intelligence blueprint so that every stage, command and governance rule is traceable from this root document.

## Project Map

| Project                   | Purpose                                                                                                        | Detailed Specification                                               |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `codex-meta-intelligence` | Multi-agent operating system that implements the Codex Meta-Intelligence blueprint and drives production work. | [codex-meta-intelligence/agent.md](codex-meta-intelligence/agent.md) |
| `agents/`                 | Legacy Python agents that power notebook-based experiments.                                                    | [agents/README.md](agents/README.md)                                 |
| `macro_system/`           | Macro orchestration prototypes that predate the Meta-Intelligence stack.                                       | [macro_system/README.md](macro_system/README.md)                     |
| `cursor/`                 | Cursor IDE integration utilities and launch scripts.                                                           | [cursor/README.md](cursor/README.md)                                 |

The Codex Meta-Intelligence project is the canonical implementation moving forward. All new agent work should be developed there unless an explicit exception is recorded in `ROADMAP.md`.

## Blueprint Integration Checklist

To ensure the repository adheres to the Codex Meta-Intelligence blueprint, every agent initiative must account for the following facets before work begins:

1. **Dynamic Setup & Commands** – Validate that `stage.json` reflects the current stage, run `./codex-meta-intelligence/build.sh`, and align any additional tooling with the slug-based directory scheme. Ensure Cursor automation scripts in `scripts/` are enabled when performing coding tasks.
2. **Directory & Spec Parity** – Cross-check the Markdown specs at the repository root with the `src/` implementations so that no placeholder files remain. Each new agent, macro or protocol must have both documentation and code updated together.
3. **Stage Execution Discipline** – Stage promotion is exclusively handled by the build script. If a stage advancement occurs, document the change in the PR summary and update relevant metadata sections in Stage files.
4. **Testing & Quality Gates** – Execute the quality commands declared in the applicable `AGENTS.md` files (e.g., `pnpm --filter codex-meta-intelligence lint|test|typecheck|build`) and capture telemetry via the analytics modules.
5. **Security, Performance & Context Governance** – Incorporate sandboxing, context governance and performance constraints referenced in the blueprint before agents are marked production ready.
6. **Continuous Improvement Hooks** – Consider variant analyses, foresight predictions and proactive improvement opportunities from the blueprint when designing new capabilities; log resulting decisions in the relevant project documentation.

## Top Ten Enhancement Tracks

These tracks represent the most leveraged improvements identified across the blueprint review. When updating any agent-facing system, address the applicable track(s) and record the work in project documentation and changelogs.

### 1. Stage Automation Integrity

- Run `pnpm install --filter codex-meta-intelligence...` before invoking `./codex-meta-intelligence/build.sh` so stage tasks have all toolchains available.
- Execute `./codex-meta-intelligence/build.sh --dry-run` (if added) or read its logs to verify `stage.json` transitions and metadata stamps. Log deviations in PR descriptions.
- Keep `stage.json` immutable outside the build script; repairs must document cause and remediation steps in `ROADMAP.md` or the affected stage spec.

### 2. Cursor Compliance & Enforcement

- Start every coding session with `python scripts/auto_setup_cursor.py` or the pnpm aliases in `package.json` to guarantee Cursor automation, enforcement hooks and compliance reporting are active.
- Confirm `src/cursor/{auto_invocation,enforcement}.py` (and associated TypeScript helpers) are in sync with the enforcement instructions contained in the blueprint and AGENT docs.
- Capture Cursor compliance output (success percentage, triggered files, enforcement status) in PR notes when agent automation is modified.

### 3. Knowledge & Brain-Block Synchronisation

- Verify the NDJSON datasets listed in the custom environment variables are available before enabling auto-loaders.
- Run `python -m src.knowledge.auto_loader status` (or equivalent CLI) to confirm watchers ingest updates and surface metrics in `data/knowledge/`.
- Document schema revisions for knowledge blocks in `knowledge.md` and ensure associated tests in `tests/knowledge` cover parsing and freshness detection.

### 4. Mobile Control Workflow

- Exercise the mobile control layer via `python -m src.mobile.mobile_app` to validate goal creation, approval and notifications.
- When modifying mobile integrations, coordinate updates with Cursor enforcement so remote approvals continue to gate automated coding flows.
- Surface mobile telemetry (goal counts, approvals, latency) through the analytics stack and include the resulting dashboards in Stage documentation.

### 5. Context Fabric & Governance

- Keep `src/context/{fabric,orchestrator,governance}.ts` consistent with `context.md` by documenting ingest/index/compose/evaluate behaviours for every stage.
- Run governance audits after sensitive changes using any provided CLI (e.g., `pnpm --filter codex-meta-intelligence context:audit`) to confirm PII masking and access controls remain intact.
- Capture context-selection rationales in memory logs so foresight and operator reviews can trace decisions.

### 6. Macro & Meta-Agent Orchestration

- Ensure macros defined in `src/macro/scripts.ts` reflect the Execution Pipeline order and include fallbacks for failure modes documented in the blueprint.
- Keep the meta-agent scheduler and state store aligned with policy decisions (priority weighting, fairness constraints); update `metaagent.md` whenever algorithms change.
- Extend test coverage in `tests/metaagent` and `tests/macro` for new orchestration features, including failure/retry logic.

### 7. Telemetry, Performance & Capacity Planning

- Update `src/analytics/{metrics,tracing}.ts` whenever new metrics or spans are introduced and document dashboards or alerts in `foresight.md` or `README.md`.
- Run load or smoke tests (e.g., `pnpm --filter codex-meta-intelligence test -- --runInBand` plus any Artillery/Locust scripts) after major concurrency changes.
- Record resource budgets and scaling policies in the project documentation so operators can reconcile telemetry deviations quickly.

### 8. Security & Compliance Hardening

- Execute dependency and secret scans (`pnpm audit`, `python -m ruff check`, `npm audit` for auxiliary packages) as part of the QA cycle; store results in audit logs when security-facing modules change.
- Align encryption, authentication and sandbox modules with `security/{scanner,encryption,auth}.ts`; stage-specific hardening notes belong in `SECURITY.md`.
- Document third-party service access (Slack, GitHub, email) and ensure credentials are managed through sanctioned vault mechanisms.

### 9. Quality Assurance & Testing Discipline

- Maintain parity between documentation updates and automated tests—new behaviour must ship with Jest, integration or Playwright coverage as defined per stage.
- Follow linting and formatting standards for both TypeScript (`pnpm lint`) and Python (`python -m ruff check`) when relevant files change.
- Capture test evidence (command output, coverage metrics) in PR descriptions when touching critical workflows or stage progression tooling.

### 10. Continuous Improvement & Variant Tracking

- Periodically revisit the variant analyses (event-driven, service mesh, monolith, etc.) and record adoption/deferral decisions in `EXPONENTIAL_IMPROVEMENT_SUMMARY.md` or project READMEs.
- Use foresight predictions to justify major architectural changes, logging hypotheses and outcomes for future retrospectives.
- Keep the opportunity backlog synchronised across `AGENT.md`, `agent.md` and relevant specs so contributors can pick up vetted initiatives without rediscovery work.

## Governance Principles

1. **Single Source of Truth** – Each project maintains its own `agent.md`/`AGENTS.md` pair. This root document records ownership and points to the authoritative specs.
2. **Context Engineering Compliance** – Before an agent runs, it must merge AGENT/AGENTS guidance from the repository root, the project root and the target directory. The TypeScript implementation lives in `codex-meta-intelligence/src/agent/reader.ts`.
3. **Cursor Enforcement** – Cursor integration scripts under `scripts/` must be invoked before automated coding tasks. Refer to `scripts/auto_setup_cursor.py` for the end-to-end bootstrap pipeline and ensure enforcement hooks remain up to date with blueprint requirements.
4. **Testing & Quality Gates** – Every agent workflow must execute the commands declared in the applicable `AGENTS.md` file. For the Meta-Intelligence stack this includes `pnpm lint`, `pnpm test`, `pnpm typecheck` and `pnpm build` as part of Stage 1.
5. **Telemetry** – Agents publish execution traces through `codex-meta-intelligence/src/analytics/{metrics,tracing}.ts` so that operator dashboards and automated monitors receive consistent signals. Stage-specific dashboards (Stage 2 foresight, Stage 3 resilience) should be updated whenever telemetry schemas evolve.

## Stage Alignment Summary

- **Stage 1 (Core Functionality)** – Establish scaffolding, AGENTS.md parsing, in-memory context fabric and baseline protocols. Confirm that each spec file and skeleton implementation is present and that the build script remains idempotent.
- **Stage 2 (System Refinement)** – Implement full agent logic, persistent storage, open protocol adapters and security hardening. Ensure documentation tracks the introduction of message brokers, hybrid retrieval and predictive scheduling.
- **Stage 3 (Polishing & Elevation)** – Deliver UI, plugin architecture, resilience tooling and fairness modules. Keep this file synchronised with plugin registry updates, ethical guardrails and chaos engineering practices.

## Continuous Improvement Signals

- **Variant Analyses** – Document when architecture variants (event-driven, service mesh, monolith) are evaluated, adopted or deferred. Capture the rationale in project-specific docs to avoid repeating investigations.
- **Opportunity Backlog** – When proactive improvement items (adaptive scheduling, cost control, sustainability metrics, etc.) are actioned, record the decision path and link to implementation notes in the relevant project README or spec.
- **Cross-Project Dependencies** – Whenever knowledge systems, mobile control or brain-block integrations change, ensure dependent directories (`cursor/`, `knowledge/`, `mobile/`) receive corresponding updates.

## When to Update This File

Update this document whenever a new agent-focused project is added to the repository, when a project is deprecated, when ownership changes, or when blueprint guidance is revised. Include cross-references to the authoritative specs so that downstream agents (and human operators) can locate rule changes quickly.
