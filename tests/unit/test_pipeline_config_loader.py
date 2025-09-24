"""
SECTION 1: Header & Purpose
- Unit tests validating configuration loading and schema enforcement.
"""

# SECTION 2: Imports / Dependencies
from pathlib import Path

import pytest

from src.common.config_loader import (
    ConfigValidationError,
    MetricsConfig,
    PipelineConfig,
    load_config,
)

# SECTION 3: Types / Interfaces / Schemas
# - Tests rely on PipelineConfig and MetricsConfig schemas defined in config_loader.

# SECTION 4: Core Logic / Implementation


def test_load_pipeline_config_success(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
        training:
          dataset:
            path: data/sample.csv
            target_column: label
            feature_columns: [a, b]
            validation_split: 0.2
            stratify: true
            random_state: 42
          experiment:
            tracking_uri: ./mlruns
            registry_uri: ./mlruns
            experiment_name: test-exp
            run_name: test-run
          model:
            framework: pytorch
            hyperparameters:
              epochs: 5
              learning_rate: 0.1
              batch_size: 8
        inference:
          default_model_name: demo
          cache_ttl_seconds: 60
          max_batch_size: 32
          concurrency_limit: 4
        """
    )

    config = load_config(config_path, PipelineConfig)
    assert config.training.dataset.target_column == "label"
    assert config.inference.max_batch_size == 32


def test_load_config_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "absent.yaml"
    with pytest.raises(ConfigValidationError):
        load_config(missing, PipelineConfig)


def test_metrics_config_validation(tmp_path: Path) -> None:
    config_path = tmp_path / "metrics.yaml"
    config_path.write_text(
        """
        core_metrics:
          accuracy:
            minimum: 0.8
        fairness_metrics:
          statistical_parity_difference:
            minimum: -0.1
            maximum: 0.1
        """
    )
    metrics = load_config(config_path, MetricsConfig)
    assert "accuracy" in metrics.core_metrics
    assert metrics.fairness_metrics["statistical_parity_difference"].maximum == 0.1


# SECTION 5: Error & Edge Case Handling
# - Tests missing file scenario ensuring ConfigValidationError raised.
# - Validation test ensures fairness thresholds parsed correctly.


# SECTION 6: Performance Considerations
# - Tests operate on tmp files; negligible performance impact.


# SECTION 7: No additional exports for test modules.
