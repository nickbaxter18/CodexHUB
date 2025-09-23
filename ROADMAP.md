# AI Pipeline Roadmap

## Completed in This Iteration

- Established configuration schemas and loaders with validation for training, inference, metrics, and governance settings.
- Implemented training data ingestion, metric evaluation, fairness diagnostics, privacy scrubbing, MLflow registry integration, and inference services with caching.
- Added comprehensive unit, integration, and compliance tests plus documentation updates linking to governance artefacts.

## Next Priorities

1. **Training Orchestration:** Build `src/training/train.py` to orchestrate end-to-end training leveraging the new modules and logging artefacts to MLflow.
2. **Monitoring Layer:** Implement `src/inference/monitoring.py` for drift detection and latency tracking using Prometheus-compatible metrics.
3. **Model Cards:** Deliver automated model card generation in `src/governance/model_card_generator.py` tied to governance configs and stored under `docs/model_cards/`.
4. **CI Enhancements:** Extend GitHub Actions to run the new Python test suites and integrate governance compliance checks into pipelines.

## Risk Tracking

- **Dependency Weight:** MLflow adds runtime overhead; monitor installation time and consider lightweight registry fallbacks for constrained environments.
- **Fairness Data Availability:** Sensitive attribute coverage may be incomplete in upstream datasets—document gaps and align with legal guidance.
- **Scalability:** Inference concurrency controls exist, but further load testing (see `tests/performance/`) must be implemented before production rollout.
