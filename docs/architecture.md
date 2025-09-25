---
title: CodexHUB Architecture
description: High-level view of the hybrid Node.js and Python automation stack that powers CodexHUB.
---

# CodexHUB Architecture

CodexHUB combines an Express entry point, a governance-aware Python pipeline, and a dense set of automation helpers that keep Cursor IDE integrations healthy. This document mirrors the canonical [`ARCHITECTURE.md`](../ARCHITECTURE.md) outline while adding operational context for day-to-day contributors.

## Platform Overview

- **Node.js Services (`src/`)** – Hosts the default Express app (`src/index.js`) and orchestration helpers that surface automation endpoints. The service listens on `PORT` (defaults to `4000`) and exposes `/health` for liveness checks.
- **Editor & Health Bridge (`backend/`)** – Provides the `backend/health-test.js` express server that fronts the browser-based editor experience. Endpoints such as `/cursor-agent` and `/task-status` are protected by `EDITOR_API_KEY` and act as a thin shim around the `cursor-agent` command.
- **Python Governance Modules (`src/common`, `src/training`, `src/governance`, `src/registry`, `src/inference`)** – Implement schema validation, dataset handling, fairness/privacy enforcement, MLflow registry integration, and inference services. These modules are structured for deterministic runs and strongly typed using Pydantic and mypy.
- **Automation Tooling (`scripts/`, `src/cursor`, `src/knowledge`, `src/mobile`)** – Orchestrates Cursor auto-invocation, knowledge ingestion, mobile goal tracking, and performance telemetry.

## Data & Control Flow

1. **Configuration Loading** – YAML and environment variables are parsed via `src/common.config_loader`, yielding validated settings for downstream modules. Environment bundles are checked against the generated JSON Schema (`config/env.schema.json`) so CI and local runs share the same contract.
2. **Training & Evaluation** – `src/training` loads datasets, produces reproducible splits, and emits metrics. `src/governance` enforces fairness/privacy rules using thresholds defined in `config/`.
3. **Registry Management** – `src/registry.registry.MLflowRegistry` standardises run creation, metric logging, and model promotion inside MLflow.
4. **Inference Delivery** – `src/inference.inference.InferenceService` hydrates the latest registry version, guards concurrency limits, and caches predictions.
5. **Developer Feedback Loop** – Cursor auto-invocation (configurable via `CURSOR_AUTO_INVOCATION_*` variables) monitors source files and dispatches specialist agents. Performance data flows into `results/performance`, while `scripts/codex_status.py` aggregates Cursor compliance, plan counts, and telemetry snapshots for quick health checks.

## Key Integrations

- **Knowledge Systems** – `src/knowledge.auto_loader` streams NDJSON documents defined in `KNOWLEDGE_NDJSON_PATHS`, while `src/knowledge.brain_blocks_integration` offers semantic lookups for the Cursor agents.
- **Mobile Control** – `src/mobile.mobile_app` exposes goal-management endpoints that mirror the automation flow for remote approvals.
- **Performance Monitoring** – `src/performance.metrics_collector.PerformanceCollector` gathers build and agent timings. Metrics are saved to `results/performance/performance_metrics_*.json` and surfaced through the `codex:status` CLI.

## Operational Notes

- Environment defaults now live in [`.env.example`](../.env.example), covering Cursor, knowledge ingestion, mobile control, and MLflow destinations. Regenerate the schema and validator outputs with `python scripts/generate_env_schema.py` whenever the variable set evolves.
- Container builds install both Node and Python dependencies and expose port `4000` to align with the Express default. Use `docker run -p 4000:4000 codexhub` after `docker build` to mirror local behaviour.
- The Makefile centralises commands (`make lint`, `make test-python`, `make status`) to coordinate the mixed-language toolchain.
- `src/performance.cli` now supports selective skips and configurable concurrency, allowing developers to parallelise fast checks while deferring heavier audits when iterating quickly.
- GitHub Actions enforces dependency review and secret scanning on every pull request via the `PR Security Gate` workflow, supplementing the scheduled weekly audits.

Refer to [`SECURITY.md`](../SECURITY.md) for hardening guidance and the top-level [`README`](../README.md) for onboarding workflows.
