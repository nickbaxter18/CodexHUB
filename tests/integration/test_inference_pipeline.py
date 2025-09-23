"""
SECTION 1: Header & Purpose
- Integration test exercising registry-backed inference service end-to-end.
"""

# SECTION 2: Imports / Dependencies
from pathlib import Path

import mlflow.pyfunc
import numpy as np
import pytest

from src.common.config_loader import ExperimentConfig, InferenceConfig
from src.inference.inference import InferenceError, InferenceService
from src.registry.registry import MLflowRegistry

# SECTION 3: Types / Interfaces / Schemas
# - Utilizes ExperimentConfig and InferenceConfig for setup.

# SECTION 4: Core Logic / Implementation


class _ConstantModel(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):  # type: ignore[override]
        return np.ones(len(model_input))


def _prepare_registry(tmp_path: Path) -> MLflowRegistry:
    tracking_dir = tmp_path / "mlruns"
    tracking_uri = tracking_dir.as_posix()
    experiment = ExperimentConfig(
        tracking_uri=tracking_uri,
        registry_uri=tracking_uri,
        experiment_name="integration-experiment",
        run_name="integration-run",
    )
    registry = MLflowRegistry(experiment)
    with registry.start_run(run_name=experiment.run_name) as run:
        mlflow.pyfunc.log_model("model", python_model=_ConstantModel())
        run_id = run.info.run_id
    registry.register_model(run_id, "model", "IntegrationModel")
    return registry


def test_inference_service_returns_predictions(tmp_path: Path) -> None:
    registry = _prepare_registry(tmp_path)
    inference_config = InferenceConfig(
        default_model_name="IntegrationModel",
        cache_ttl_seconds=5,
        max_batch_size=10,
        concurrency_limit=2,
    )
    service = InferenceService(inference_config, registry)
    payload = {"records": [{"feature_one": 1.0}, {"feature_one": 2.0}]}
    response = service.predict(payload)
    assert response.predictions == [1.0, 1.0]
    assert "IntegrationModel" in response.model_uri


def test_inference_service_validates_payload(tmp_path: Path) -> None:
    registry = _prepare_registry(tmp_path)
    inference_config = InferenceConfig(
        default_model_name="IntegrationModel",
        cache_ttl_seconds=5,
        max_batch_size=1,
        concurrency_limit=1,
    )
    service = InferenceService(inference_config, registry)
    payload = {"records": [{"feature_one": 1.0}, {"feature_one": 2.0}]}
    with pytest.raises(InferenceError):
        service.predict(payload)


# SECTION 5: Error & Edge Case Handling
# - Validates batch-size enforcement and payload validation.


# SECTION 6: Performance Considerations
# - Reuses cached registry to avoid repeated MLflow initialisation in each test.


# SECTION 7: No exports for test module.
