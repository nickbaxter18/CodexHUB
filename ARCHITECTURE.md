# CodexHUB Governance-Integrated AI Production Pipeline Architecture

## Overview

CodexHUB's new AI pipeline introduces modular Python packages under `src/` that manage training data ingestion, metric evaluation, governance enforcement, registry integration, and inference delivery. Each module follows strict schema validation and governance-aware patterns to guarantee reproducibility, transparency, and compliance.

## Module Breakdown

- **`src/common`** – Centralises configuration schemas using Pydantic, ensuring deterministic validation for YAML configs and enforcing reproducibility guardrails.
- **`src/training`** – Provides dataset loading, stratified splitting, and deterministic metric calculations designed for MLflow logging and governance threshold checks.
- **`src/governance`** – Implements fairness and privacy utilities. Fairness metrics compute statistical parity, equal opportunity, and disparate impact with configurable enforcement. Privacy scrubbing sanitises PII in artefacts and logs.
- **`src/registry`** – Wraps MLflow tracking and registry APIs, ensuring experiments are created, metrics logged, and model versions retrieved consistently with governance tagging.
- **`src/inference`** – Supplies caching-aware inference services that validate payloads, enforce concurrency limits, and hydrate models from the registry.

## Data & Control Flow

1. **Configuration Loading** – YAML files in `config/` are parsed via `src/common.config_loader`, returning strongly typed configuration objects for downstream modules.
2. **Training Preparation** – `src/training.data_loader` ingests datasets, validates schema compliance, and outputs reproducible train/validation splits.
3. **Metric & Fairness Evaluation** – `src/training.metrics` computes canonical metrics; `src/governance.fairness` enforces fairness thresholds defined in `config/metrics.yaml` and `config/governance.yaml`.
4. **Registry Integration** – `src/registry.registry.MLflowRegistry` manages runs, logging, and model versioning within MLflow while returning URIs for inference services.
5. **Inference Execution** – `src/inference.inference.InferenceService` retrieves the latest model, maintains TTL-based caches, validates requests, and outputs predictions while respecting concurrency budgets.

## Extensibility & Future Work

- Hooks exist for distributed training integration via new orchestration layers once model training scripts are implemented.
- Governance modules expose extension points for additional fairness diagnostics or privacy scrubbing rules.
- Registry wrapper allows injection of alternative loaders (e.g., SageMaker endpoints) without altering calling code.
