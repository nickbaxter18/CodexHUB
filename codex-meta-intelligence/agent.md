# Agent Specifications

## Overview

The agent subsystem powers the Codex Meta-Intelligence platform—a multi-agent operating system that follows the three-stage blueprint described in this repository. All agents inherit from the shared base class in `src/agent/index.ts`, execute within the Harmony Protocol + Execution Pipeline, and surface telemetry through the analytics stack. Documentation and implementation are kept in lockstep so that every blueprint directive (context engineering, Cursor enforcement, security, testing and UX refinement) has a concrete owner.

## Role Matrix

| Agent               | Primary Responsibilities                                     | Stage 1 Focus                                                                                  | Stage 2 Enhancements                                                                                | Stage 3 Elevation                                                                 |
| ------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **FrontendAgent**   | Generate UI components, styling and UX artefacts.            | Provide skeleton implementation, respect styling cognition placeholders and publish telemetry. | Produce React/Vite code, enforce Tailwind/animation rules, run lint/test suites, trigger QA macros. | Integrate dashboard widgets, plugin UI modules and accessibility instrumentation. |
| **BackendAgent**    | Implement APIs, services and infrastructure automation.      | Scaffold service handlers and ensure protocol compliance stubs exist.                          | Connect to Express/FastAPI stacks, wire persistent storage, enforce security policies.              | Support resilience tooling, chaos drills and operator-driven deploy macros.       |
| **KnowledgeAgent**  | Manage knowledge block lifecycle and ingestion.              | Offer in-memory storage and ndjson scaffold validation.                                        | Integrate vector + graph stores, scoring strategies and refresh workflows.                          | Coordinate freshness monitoring, auto-updates and governance auditing.            |
| **QAAgent**         | Execute aesthetic, technical and narrative QA.               | Wire stubbed checks and pipeline integration.                                                  | Run axe-core, ESLint/Prettier, Jest/Vitest, narrative scoring; feed issues to refinement agents.    | Add UI test automation, fairness checks and plugin QA.                            |
| **RefinementAgent** | Apply iterative improvements and styling cognition feedback. | Provide hook for refinement loop invocation.                                                   | Implement styling adjustments, rerun QA and document diffs.                                         | Collaborate with operator UI to support explainability and fairness adjustments.  |

All contracts are defined in `src/agent/types.ts` and validated using Ajv. Agents remain pure TypeScript modules with named exports.

## Dynamic Setup & Command Flow

1. **Stage Detection** – `build.sh` reads `stage.json` to determine which scaffolding or implementation tasks to run. Agents should never bypass this script; it guarantees directory structures, spec files and tests stay synchronised with the blueprint.
2. **Cursor Integration** – Automated coding tasks must invoke `scripts/auto_setup_cursor.py` (or its pnpm aliases) prior to execution. The enforcement helpers from `src/cursor` ensure proper agent selection per file type.
3. **Environment Bootstrapping** – Upon initialisation, each agent merges AGENTS.md directives via `src/agent/reader.ts`, installs dependencies using pnpm where required, and configures telemetry exporters.
4. **Command Execution** – After any code change, agents run the quality gates listed in the merged guidance. For Stage 1 this includes `pnpm lint`, `pnpm test`, `pnpm typecheck` and `pnpm build`; later stages add security scanners, chaos drills and UI tests.
5. **Stage Promotion** – Successful completion of a stage updates `stage.json` through the build script. Human operators must record the promotion in PR summaries, update metadata blocks and ensure documentation (including this file) reflects the new capabilities.

## Execution Lifecycle

1. **Task Scheduling** – The meta-agent enqueues tasks, selects macros and posts an `AgentMessage` to the broker/event bus.
2. **Guideline Merge** – `AgentGuidelineReader` composes AGENTS.md, Cursor rules and context governance policies into a single instruction set for the executing agent.
3. **Context Preparation** – Agents request context packets through the Context Fabric (`src/context/{fabric,orchestrator}.ts`), ensuring ingest → normalise → index → retrieve → compose → evaluate → persist is respected.
4. **Execution Pipeline** – Agents honour the Draft → Audit → Refinement → Elevation → Delivery → Deploy flow implemented in `src/protocol/execution.ts`. Harmony conflict resolution (`src/protocol/harmony.ts`) arbitrates conflicting artefacts.
5. **Result Handling** – `AgentResult` objects include status, artefacts, QA findings, context updates, metrics and optional escalation reasons. Failures trigger retries, alternative macros or operator intervention based on policy.

## Improvement Playbooks (Top Ten Focus Areas)

Each playbook captures concrete upgrade work identified during the blueprint review. Apply the relevant playbook(s) whenever enhancing the platform and document outcomes in specs, tests and telemetry notes.

### 1. Stage Automation Integrity

- **Scope** – `build.sh`, `stage.json`, stage metadata sections in `stage*.md` and `README.md`.
- **Actions** – Run `pnpm install --filter codex-meta-intelligence...` before invoking `./build.sh`; ensure the script logs promotions, completion metadata and recovery guidance. Add integration tests (e.g., `tests/build.spec.ts`) that guard against missing directories or unsynchronised specs.
- **Documentation** – Capture stage changes in PR summaries and update the relevant stage spec with completion evidence and outstanding follow-ups.

### 2. Cursor Compliance & Enforcement

- **Scope** – `src/cursor/{auto_invocation,enforcement}.py`, `src/cursor/sync.ts`, `scripts/auto_setup_cursor.py`.
- **Actions** – Exercise `python scripts/auto_setup_cursor.py` (or `pnpm run cursor:auto`) to validate compliance metrics and agent selection logic. Keep default agent mappings consistent with the enforcement instructions and document overrides in `cursor.md`.
- **Testing** – Expand `tests/cursor.integration.spec.ts` to assert enforcement hooks reject non-compliant flows and to snapshot compliance reports.

### 3. Knowledge & Brain-Block Synchronisation

- **Scope** – `src/knowledge/{index,storage,scaffolds}.ts`, `src/knowledge/auto_loader.py`, NDJSON assets referenced by environment variables.
- **Actions** – Validate schema migrations against representative NDJSON fixtures, logging results in `knowledge.md`. Implement freshness tests that cover watcher restarts and ensure `KnowledgeService` surfaces provenance metadata for foresight analytics.
- **Telemetry** – Emit ingestion metrics (count, latency, failure reasons) via `src/analytics/metrics.ts` and expose dashboards for operators.

### 4. Mobile Control Workflow

- **Scope** – `src/mobile/mobile_app.py`, auxiliary modules in `src/mobile`, meta-agent hooks in `src/metaagent/state.ts`.
- **Actions** – Wire mobile approvals into the meta-agent scheduler so automation respects operator decisions. Document event schemas and user flows in `operator.md` and `README.md`.
- **Testing** – Add contract tests for goal creation/approval events and, where feasible, CLI or Playwright smoke tests that exercise remote approvals.

### 5. Context Fabric & Governance

- **Scope** – `src/context/{fabric,orchestrator,governance}.ts`, `context.md`.
- **Actions** – Keep ingest/index/retrieve/compose/evaluate steps aligned with blueprint diagrams and record evaluation scores (relevance, freshness, diversity) for each retrieval. Log governance policy versions in memory for auditability.
- **Testing** – Introduce property-based tests ensuring retrieved packets satisfy governance filters and produce traceable reasoning chains.

### 6. Macro & Meta-Agent Orchestration

- **Scope** – `src/macro/{index,scripts}.ts`, `src/metaagent/{scheduler,state,monitor}.ts`, `macro.md`, `metaagent.md`.
- **Actions** – Maintain declarative Draft→Deploy sequences with explicit fallbacks. Update scheduler policies (priority weighting, fairness, escalation) alongside documentation.
- **Testing** – Expand integration suites to simulate retries, dead-letter queues and operator escalations; assert telemetry captures throughput, latency and success trends.

### 7. Telemetry, Performance & Capacity Planning

- **Scope** – `src/analytics/{metrics,tracing}.ts`, `foresight.md`, `SECURITY.md` (monitoring constraints).
- **Actions** – Define metric names and labels prior to implementation, update dashboards/alerts accordingly, and capture foresight predictions influencing scheduling.
- **Testing** – Add performance smoke tests for high-load macros and verify exporters do not block critical execution paths.

### 8. Security & Compliance Hardening

- **Scope** – `src/security/{scanner,encryption,auth}.ts`, CI definitions in `cicd/`.
- **Actions** – Integrate dependency and secret scans (`pnpm audit`, `python -m ruff check`, bespoke scripts) into the build pipeline. Document key rotation, credential handling and sandbox constraints in `SECURITY.md` whenever updated.
- **Testing** – Capture scan artefacts, enforce failing builds for high-severity findings and include regression tests for authentication/authorisation flows.

### 9. Quality Assurance & Testing Discipline

- **Scope** – `src/qa/*`, `tests/*`, QA sections of the blueprint specs.
- **Actions** – Synchronise QA thresholds (accessibility ratios, coverage minimums, fairness baselines) with documentation. Every behavioural change requires Jest/Vitest coverage plus lint/typecheck confirmations.
- **Documentation** – Update `qa.md` with threshold rationales and summarise QA outputs in PR summaries.

### 10. Continuous Improvement & Variant Tracking

- **Scope** – Variant analyses, foresight backlog, `EXPONENTIAL_IMPROVEMENT_SUMMARY.md`.
- **Actions** – When experimenting with variants (event-driven, service mesh, monolith, plugin microfrontends, etc.), record hypothesis, metrics, outcome and follow-up decisions. Feed learnings into scheduler heuristics and macro definitions.
- **Testing** – Ensure experimental code paths are feature-flagged with automated tests covering activation/deactivation scenarios; retire or document deprecated variants promptly.

## Protocols & Integrations

- **Harmony Protocol** – Resolves file/state conflicts, applies prioritisation rules and emits escalation hooks for operator review.
- **Execution Pipeline** – Provides stage functions that macros orchestrate. Agents should call `runStage` helpers rather than hard-coding stage transitions.
- **Styling Cognition** – `src/protocol/styling.ts` encodes U-DIG IT’s cognitive laws. Frontend and refinement agents must consume its validators before finalising artefacts.
- **Open Protocols** – `src/protocol/open-protocols.ts` documents MCP, ACP, A2A, ANP and AG-UI integration points. Stage 2 implements adapters; Stage 3 exposes APIs via the dashboard.
- **Cursor & IDE Sync** – `src/cursor/{adaptor,sync}.ts` merge Cursor rules with AGENTS.md, reconcile file changes and enforce compliance metrics.

## Context & Knowledge Handling

- **Knowledge Blocks** – Use `src/knowledge/{index,storage,scaffolds}.ts` to store and retrieve structured knowledge with provenance metadata. Stage 1 uses in-memory storage; Stage 2 adds vector/graph persistence; Stage 3 adds freshness monitoring and automated refresh agents.
- **Memory Systems** – `src/memory/{index,logs,cache}.ts` capture episodic records, rotate logs and expose LRU caches. Agents must log meaningful events for foresight analytics.
- **Context Governance** – `src/context/governance.ts` enforces security, PII masking and access policies. Every context request should specify the requesting agent role and intent so governance can audit decisions.

## Security, Resilience & Performance

- **Sandboxing** – Agents execute within isolated environments with limited permissions; Stage 2 introduces hardened containers (gVisor/Firecracker), and Stage 3 adds chaos/health checks.
- **Input Validation** – Ajv schema validation protects against malformed messages. Suspected prompt-injection attempts are logged and escalated.
- **Telemetry** – Metrics and traces emitted through `src/analytics/{metrics,tracing}.ts` power foresight predictions, autoscaling and operator dashboards.
- **Performance Controls** – Concurrency limits, streaming outputs and throttling protect resources. Stage 2 integrates broker-level backpressure; Stage 3 layers autoscaling and disaster recovery procedures.

## Testing & Validation

- **Unit Tests** – Located in `tests/`; cover message handling, guideline merging, context orchestration and pipeline transitions.
- **Integration Tests** – Simulate macro execution across agents, verifying Draft → Deploy progression, harmony conflict resolution and telemetry capture.
- **Security & Compliance Tests** – Include dependency scanning, secret detection and sandbox enforcement. Stage 2+ add DAST, rate-limit tests and chaos experiments.
- **UI/Plugin Tests** – Stage 3 introduces Playwright coverage for dashboard components and plugin isolation checks.

Always run the pnpm commands listed in the root `AGENTS.md` after modifications. Additional tests specific to later stages (load tests, fairness metrics, resilience drills) must be invoked when their corresponding features change.

## Stage Roadmap & Traceability

- **Stage 1 Metadata** – Ensure skeleton files exist, telemetry hooks are wired and the build script remains idempotent. Document current stage in `stage.json` and confirm metadata reflects passing tests.
- **Stage 2 Metadata** – Track message broker configuration, persistent storage schemas, protocol adapters, security hardening and Cursor/IDE integration updates. Update this file with implementation references.
- **Stage 3 Metadata** – Record dashboard modules, plugin system state, resilience tooling, fairness checks and ethics/governance controls. Maintain links to UI specs and operator workflows.

## Continuous Improvement & Opportunities

The blueprint identifies ongoing optimisation paths (adaptive scheduling, cost control, sustainability metrics, knowledge freshness, collaborative workflows, decentralised deployment, etc.). When these initiatives progress:

1. Update the relevant sections above with architectural decisions, command updates and testing obligations.
2. Record the change in the appropriate spec (`macro.md`, `protocol.md`, `context.md`, etc.) and reference that spec here for discoverability.
3. Ensure foresight analytics and telemetry dashboards ingest any new metrics required to evaluate the improvement.

Keeping this document synchronised with the blueprint guarantees that every agent implementation, test strategy and operational control remains transparent and actionable across the Codex Meta-Intelligence platform.
