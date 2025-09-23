"""
SECTION 1: Header & Purpose
- MLflow integration layer providing registry, tracking, and retrieval utilities.
- Centralises governance-aware interactions with the experiment store.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
from typing import Any, Callable, Mapping, Optional

import mlflow
from mlflow.client import MlflowClient

from src.common.config_loader import ExperimentConfig

# SECTION 3: Types / Interfaces / Schemas


class RegistryError(RuntimeError):
    """Raised when registry operations fail."""


# SECTION 4: Core Logic / Implementation


class MLflowRegistry:
    """Wrapper around MLflow tracking and model registry APIs."""

    def __init__(
        self,
        experiment_config: ExperimentConfig,
        client: Optional[MlflowClient] = None,
        model_loader: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self._experiment_config = experiment_config
        self._client = client or MlflowClient(
            tracking_uri=experiment_config.tracking_uri,
            registry_uri=experiment_config.registry_uri,
        )
        self._model_loader = model_loader or mlflow.pyfunc.load_model
        mlflow.set_tracking_uri(experiment_config.tracking_uri)
        mlflow.set_registry_uri(experiment_config.registry_uri)
        self._experiment_id = self._ensure_experiment(experiment_config.experiment_name)

    def _ensure_experiment(self, name: str) -> str:
        existing = self._client.get_experiment_by_name(name)
        if existing:
            return existing.experiment_id
        return self._client.create_experiment(name)

    def start_run(self, run_name: str | None = None, tags: Optional[Mapping[str, str]] = None):
        return mlflow.start_run(experiment_id=self._experiment_id, run_name=run_name, tags=tags)

    def log_metrics(self, run_id: str, metrics: Mapping[str, float]) -> None:
        for key, value in metrics.items():
            self._client.log_metric(run_id, key, float(value))

    def log_params(self, run_id: str, params: Mapping[str, Any]) -> None:
        for key, value in params.items():
            self._client.log_param(run_id, key, value)

    def register_model(self, run_id: str, artifact_path: str, model_name: str) -> str:
        model_uri = f"runs:/{run_id}/{artifact_path}"
        try:
            model_version = mlflow.register_model(model_uri=model_uri, name=model_name)
        except Exception as exc:  # noqa: BLE001 - Propagate as registry-specific error
            raise RegistryError(str(exc)) from exc
        return str(model_version.version)

    def latest_model_uri(self, model_name: str) -> str:
        versions = self._client.search_model_versions(filter_string=f"name='{model_name}'")
        if not versions:
            raise RegistryError(f"No model versions found for {model_name}")
        latest = max(versions, key=lambda version: int(version.version))
        return f"models:/{model_name}/{latest.version}"

    def load_model(self, model_uri: str) -> Any:
        return self._model_loader(model_uri)


# SECTION 5: Error & Edge Case Handling
# - Wraps MLflow exceptions in RegistryError for clarity.
# - Raises RegistryError when requesting models that do not exist.
# - Ensures experiment existence before logging to avoid runtime surprises.


# SECTION 6: Performance Considerations
# - Relies on MlflowClient for efficient batching of metrics and params.
# - Encourages callers to reuse MLflowRegistry instances to avoid repeated experiment resolution.


# SECTION 7: Exports / Public API
__all__ = ["MLflowRegistry", "RegistryError"]
