# Meta Agent v2

## Purpose and Scope

Meta Agent v2 is the executive control plane for the Codex ecosystem. It aggregates QA
signals, arbitrates conflicting judgments, curates trust scores, observes macro health, and
proposes governance amendments when systemic drift is detected. The component harmonizes
Frontend, Backend, Architect, QA, and Macro Orchestrator agents by ensuring a single
source-of-truth for QA outcomes.

## Architecture Overview

- **MetaAgent** — Coordinates subsystem engines, subscribes to the QA event bus, records
  causal traces, and publishes arbitration decisions.
- **TrustEngine** — Maintains Bayesian-style trust scores with an append-only journal and
  periodic snapshot compaction so trust survives restarts even during crashes.
- **ArbitrationEngine** — Normalizes conflicting events and resolves winners using trust
  weights and governance priorities loaded from `config/governance_rules.json` when
  available.
- **DriftDetector** — Observes sliding windows of QA events, flags repeated failures or
  disables, and emits amendment proposals for QA.md/AGENTS.md.
- **FallbackManager** — Invokes predefined macros when primary macros fail chaos or
  resilience thresholds.
- **MacroDependencyManager** — Tracks macro dependency schemas, blocks macros on
  incompatibilities, persists state to disk, and emits structured diff metadata when
  dependencies change.
- **QAEventBus** — Asynchronous publish/subscribe broker with correlation IDs and
  delivery metrics so arbitration, drift, and macro notifications never block one another.

## Data Flow

1. Agents publish standardized QA events (`qa_success` / `qa_failure`) via the event bus.
2. MetaAgent consumes each event, sanitizes payloads (validating numeric ranges and
   required identifiers), normalizes status synonyms (e.g., success/pass/fail), updates
   trust scores, and forwards the event—complete with a
   correlation ID—to the ArbitrationEngine queue.
3. When multiple judgments exist for the same metric, the ArbitrationEngine resolves a
   winner based on trust × governance priority, captures the confidence gap, and emits an
   audit log entry plus a `qa_arbitration` event.
4. DriftDetector records every outcome; if repeated failures or disables cross the
   configured threshold, it emits a drift proposal broadcast through `qa_drift` events for
   human governance review.
5. MacroDependencyManager listens to macro definition and dependency update events,
   blocking or unblocking macros when schema compatibility changes. It publishes
   `macro_blocked`/`macro_unblocked` events enriched with dependency diffs for
   orchestrators and persists compatibility state for replay.
6. FallbackManager executes resilience macros whenever metrics exceed thresholds to ensure
   continuous operation during chaos experiments or outages.

## Governance Integration

- Governance rules are externalized in JSON, enabling compliance reviewers to adjust agent
  priorities without touching code.
- Arbitration decisions are persisted as JSON Lines (defaulting to `logs/arbitrations.jsonl`)
  for auditability, and publish a `qa_arbitration_log_error` diagnostic if disk writes fail.
- Macro compatibility changes emit explicit `macro_blocked`/`macro_unblocked` events,
  enabling orchestrators to pause or resume workflows as dependencies evolve.
- Drift proposals surface suggested amendments to QA.md and AGENTS.md with severity,
  failure counts, and recommended document sections, but require human ratification before
  enforcement.

## Security & Privacy

- Event payloads are sanitized to avoid leaking secrets into logs and always carry
  correlation IDs for traceability.
- Trust and arbitration logs are stored on disk with directories created explicitly to
  avoid accidental path traversal.
- The system assumes authenticated agents publish events; additional verification should be
  layered at the bus boundary for production deployments.

## Resilience & Chaos Engineering

- Chaos experiments can publish simulated failures to validate fallback macros while the
  asynchronous bus ensures other arbitration streams continue unhindered.
- Drift detection catches repeated test disables or sudden coverage loss.
- Trust recalibration ensures unreliable agents lose authority until their performance
  recovers.

## Extensibility

- Engines are composed via dependency injection, enabling alternative trust models,
  arbitration policies, or drift algorithms without modifying MetaAgent core logic.
- Additional event types (e.g., `qa_warning`, `qa_exemption`) can be integrated by
  extending the event bus subscriptions.

## Operational Guidance

- Persist trust scores and arbitration logs on durable storage to survive restarts.
- Review drift proposals regularly and amend governance documents when warranted.
- Monitor the size of arbitration logs and rotate as part of operational hygiene.
