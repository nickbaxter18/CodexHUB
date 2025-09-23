# Codex QA Constitution

## 1. Purpose & Scope
- Establish a shared quality framework for all Codex agents and macro orchestrators.
- Provide a human-readable companion to the machine-readable rules in `config/qa_rules.json`.
- Ensure transparency, explainability, and continuous improvement for every generated artifact.

## 2. Governing Principles
1. **Single Source of Truth** – QA rules are centrally managed and versioned.
2. **Budget Accountability** – Each agent must respect explicit performance, reliability, and quality budgets.
3. **Event-Driven Oversight** – QA results are communicated via the `QAEventBus` to promote loose coupling.
4. **Explainability & Trust** – Failures are recorded with clear reasons; trust scores evolve based on behaviour.
5. **Self-Healing Evolution** – Repeated failures trigger retrospectives, rule refinements, and macro updates.

## 3. Agent Budgets & Test Expectations
| Agent      | Key Budgets                        | Mandatory Tests                          |
| ---------- | ---------------------------------- | ---------------------------------------- |
| Frontend   | Lighthouse score ≥ 90, Accessibility pass required | `jest_unit`, `axe_core_a11y`, `lighthouse` |
| Backend    | API latency p95 ≤ 300 ms           | `pytest_unit`, `api_fuzz`, `contract`    |
| Architect  | Dependency graph integrity         | `schema_validation`, `macro_dependency`  |
| QA         | Holistic QA sign-off               | `full_suite`                             |

> **Test Execution Enforcement** – Agents must report the tests they executed. Missing any mandatory tests will trigger a `tests_required` arbitration decision and remediation guidance to run the outstanding checks. Task payloads surface `qa_tests_executed` and a JSON-safe `qa_evaluation_payload`, enabling Agent MD, macro orchestrators, and external dashboards to compare executed versus missing tests without Python-specific serialization.

### 3a. Metric Policies & Remediation Macros
- Each agent budget now includes optional `metrics` metadata describing comparison behaviour (`gte`, `lte`, `eq`), severity weightings, remediation steps, and remediation macros.
- The QA engine surfaces these policies in every `QAEvaluation.metric_violations` entry, empowering orchestrators to map failing metrics directly to macro automation.
- Recommended macros (e.g. `::frontendgen-access`, `::perfprofile`) are emitted via `QAEvaluation.remediation_macros`, bubbled to agent results (`qa_recommended_macros`) and propagated through the MetaAgent for coordinated self-healing. `QAEngine.list_all_remediation_macros()` exposes the union of referenced macros so macro orchestrators can confirm coverage.

### 3b. Severity Scoring & Coverage Drift Detection
- Every `QAEvaluation` now includes a numeric `severity` score with a corresponding `severity_level` (`none`, `low`, `medium`, `high`). Scores are derived from metric policy weights, missing-test penalties, and exception handling paths.
- The MetaAgent escalates any `high` severity outcome even without conflicting prior signals and marks `medium` failures as `remediation_required` to prioritise macro intervention.
- Task results also surface `qa_untracked_metrics` when agents emit metrics without explicit budgets. The QA engine attaches remediation guidance to register coverage for these signals, preventing drift between observed metrics and governed thresholds.

## 4. Macro Quality Requirements
Every macro must include the following fields:
- `inputs`: Data prerequisites and assumptions.
- `outputs`: Deterministic description of expected artefacts.
- `failure_cases`: Known limitations and fallback plans.
- `dependencies`: Referenced modules, APIs, or services.
- `context`: Default environments (`dev`, `staging`, `prod`).

Macros missing required fields are rejected by the `QAEngine`. Additional context such as `state_change` or `rollout_plan` is encouraged when available.

> **Macro Validation API** – Call `QAEngine.assess_macro_definition()` to receive a structured `MacroValidationResult` covering missing or empty fields, out-of-policy contexts, recommended remediation steps, and the canonical environment list. This enables cross-language orchestrators to surface actionable validation errors without needing to understand the underlying JSON rules.

### 4a. Macro Catalog Governance
- Invoke `QAEngine.audit_macro_catalog(available_macros)` to reconcile remediation macros listed in QA rules with the live macro registry (e.g. Macro Engine JSON). The audit flags missing remediation macros per agent, surfaces the union of required macros, and lists available macros not currently referenced, preventing drift between QA policy and macro coverage.
- Arbitration payloads include both `recommended_macros` and `tests_executed`, ensuring macro orchestrators can trigger the correct recovery sequences and verify that remediation automation executes the promised tests.

## 5. Event Lifecycle
1. **Agent Execution** – Agents run tasks through `Agent.run_with_qa`.
2. **Budget Evaluation** – Metrics are compared against budgets via the `QAEngine`.
3. **Structured Assessment** – `QAEngine.assess_task_result` emits a `QAEvaluation` object containing trust deltas, severity scoring, remediation guidance, executed and missing test inventories, untracked metric indicators, and failure history. `QAEvaluation.to_dict()` and the propagated `qa_evaluation_payload` guarantee a stable cross-language representation for API and event consumers.
4. **Event Publication** – Success and failure evaluations are published to the `QAEventBus`.
5. **Meta Arbitration** – The `MetaAgent` analyses successive events for conflicts, flags missing test execution with a `tests_required` decision, escalates repeated failures, and emits `qa_arbitration` decisions that include macro-trigger recommendations and weighted remediation playbooks.
6. **Continuous Improvement** – Recorded failures drive remediation work items and rule updates.

## 5a. Runtime Refresh & Health Reporting
- `QAEngine.refresh_from_source()` reloads the JSON rules and schema at runtime, reconciling added or removed agents without requiring a process restart.
- `QAEngine.generate_health_report()` surfaces consolidated trust scores, outstanding failures, budget/test expectations, metric policies (thresholds, comparisons, weights), and the macros most frequently recommended for recovery.
- Exceptions raised by any agent are converted into structured `qa_failure` events and arbitration guidance, ensuring orchestrators receive actionable diagnostics even when tasks abort early.

## 6. Trust & Governance
- Trust scores start at `1.0` and are reduced by 10% (floor `0.1`) per recorded failure.
- Successful runs add `0.05` trust (ceiling `1.5`), reinforcing consistent quality.
- Overrides must be documented with justification and reviewed by the QA Agent.
- No deployment proceeds without green budgets and explicit QA sign-off.

## 7. Drift Detection & Self-Healing
- Track failure trends in `QAEngine.agent_failures` for recurring issues.
- Use `QAEngine.generate_remediation_plan()` for contextual recovery guidance after every failure.
- Escalate to Architecture when failures involve schema or dependency drift.
- MetaAgent arbitration decisions include escalation recommendations when recent success/failure signals conflict.
- Rule refresh and health report APIs enable orchestrators to recalibrate budgets dynamically as remediation tasks complete.

## 8. Future Enhancements
- Persist trust and failure history to durable storage for cross-session analytics.
- Introduce hypothesis-driven or property-based testing for macros.
- Evaluate asynchronous event processing for large-scale agent orchestration.
