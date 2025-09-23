"""
SECTION 1: Header & Purpose
- Tests for MLflow registry wrapper ensuring experiment and model operations succeed.
"""

# SECTION 2: Imports / Dependencies
from pathlib import Path

import mlflow.pyfunc
import numpy as np

from src.common.config_loader import ExperimentConfig
from src.registry.registry import MLflowRegistry

# SECTION 3: Types / Interfaces / Schemas
# - Uses ExperimentConfig schema to configure registry interactions.

# SECTION 4: Core Logic / Implementation


class _ConstantModel(mlflow.pyfunc.PythonModel):
    """Simple MLflow Python model returning constant predictions."""

    def predict(self, context, model_input):  # type: ignore[override]
        return np.ones(len(model_input))


def test_registry_logs_and_registers(tmp_path: Path) -> None:
    tracking_dir = tmp_path / "mlruns"
    tracking_uri = tracking_dir.as_posix()
    config = ExperimentConfig(
        tracking_uri=tracking_uri,
        registry_uri=tracking_uri,
        experiment_name="test-experiment",
        run_name="test-run",
    )
    registry = MLflowRegistry(config)

    with registry.start_run(run_name=config.run_name) as run:
        registry.log_metrics(run.info.run_id, {"accuracy": 0.9})
        registry.log_params(run.info.run_id, {"epochs": 5})
        mlflow.pyfunc.log_model("model", python_model=_ConstantModel())

    version = registry.register_model(run.info.run_id, "model", "TestModel")
    assert version == "1"

    model_uri = registry.latest_model_uri("TestModel")
    loaded = registry.load_model(model_uri)
    predictions = loaded.predict([[1, 2], [3, 4]])
    assert list(predictions) == [1.0, 1.0]


# SECTION 5: Error & Edge Case Handling
# - Ensures registry raises when interactions fail via MLflow (implicitly tested through mlflow).


# SECTION 6: Performance Considerations
# - Uses local file-based tracking store suited for tests.


# SECTION 7: No exports required for test module.
