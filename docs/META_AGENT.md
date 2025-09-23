# Meta Agent Architecture

## Overview

The Meta Agent coordinates cross-agent QA workflows by consuming events from the QA event bus, arbitrating conflicting outcomes,
updating trust scores, detecting drift, and orchestrating fallback macros.

## Components

- **ConfigLoader** – Validates governance, agent, and QA policy configuration using JSON Schema.
- **TrustEngine** – Maintains Bayesian-style trust scores with durable journalling.
- **ArbitrationEngine** – Resolves conflicts using governance priorities and trust weights.
- **DriftDetector** – Computes PSI/KS/KL divergence against governance reference profiles while still tracking repeated failures.
- **FallbackManager** – Maps metrics to fallback macros and triggers registered callbacks.
- **Logger** – Emits structured JSON telemetry for observability.

## Event Flow

1. QA agents publish `qa_success` or `qa_failure` events to the `QAEventBus`.
2. Meta Agent sanitises payloads, validates structure, and updates trust scores.
3. Conflicts are queued per metric and resolved via `ArbitrationEngine` using trust-weighted priorities.
4. DriftDetector evaluates statistical divergence (PSI/KS/KL) plus repeated-failure windows; detected drift emits `qa_drift` events with calibrated severity.
5. FallbackManager triggers registered macros when metrics exceed governance thresholds.
6. Structured arbitration logs are appended to `logs/arbitrations.jsonl`.

## Configuration

Use `MetaAgent.from_config(ConfigLoader(...), event_bus)` to create a fully configured instance. The loader pulls default trust
scores from `config/agents.json` and arbitration parameters from `config/governance.json`.

## Observability

- Structured logs include correlation IDs for tracing multi-event workflows.
- Trust snapshots are emitted with each arbitration decision for dashboards.
- Drift proposals include severity, agent, and metric context for follow-up actions.

## Testing

- Unit tests live in `meta_agent/tests/` covering trust updates, arbitration, fallback invocation, and drift detection.
- Repository-level tests in `tests/test_config_loader.py` and `tests/test_probabilistic_qa.py` ensure configuration and probabilistic helpers remain stable.
