"""
SECTION 1: Header & Purpose
- Provides shared configuration utilities that load and validate YAML settings.
- Supports training, inference, and governance modules with deterministic, schema-driven defaults.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Type, TypeVar

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    ValidationError,
    field_validator,
    model_validator,
)

# SECTION 3: Types / Interfaces / Schemas


class ConfigValidationError(RuntimeError):
    """Raised when configuration files fail validation."""


class DatasetConfig(BaseModel):
    """Schema describing dataset ingestion parameters."""

    path: Path
    target_column: str
    feature_columns: list[str]
    validation_split: float = Field(ge=0.0, le=0.5)
    stratify: bool = True
    random_state: int = 42

    @field_validator("feature_columns")
    @classmethod
    def _ensure_features_present(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("feature_columns must contain at least one feature")
        return value

    @field_validator("target_column")
    @classmethod
    def _ensure_target_non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("target_column cannot be empty")
        return value


class ModelHyperparameters(BaseModel):
    """Schema representing framework-agnostic hyperparameters."""

    epochs: PositiveInt
    learning_rate: float = Field(gt=0.0)
    batch_size: PositiveInt


class ModelConfig(BaseModel):
    """Schema describing model metadata and hyperparameters."""

    framework: str
    hyperparameters: ModelHyperparameters


class ExperimentConfig(BaseModel):
    """Schema describing MLflow experiment configuration."""

    tracking_uri: str
    registry_uri: str
    experiment_name: str
    run_name: str


class TrainingConfig(BaseModel):
    """Aggregate training configuration."""

    dataset: DatasetConfig
    experiment: ExperimentConfig
    model: ModelConfig


class InferenceConfig(BaseModel):
    """Schema for inference runtime configuration."""

    default_model_name: str
    cache_ttl_seconds: PositiveInt
    max_batch_size: PositiveInt
    concurrency_limit: PositiveInt


class MetricThreshold(BaseModel):
    """Represents allowable bounds for a metric value."""

    model_config = ConfigDict(extra="forbid")
    minimum: float | None = None
    maximum: float | None = None

    @model_validator(mode="after")
    def _validate_bounds(self) -> "MetricThreshold":
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum")
        return self


class MetricsConfig(BaseModel):
    """Schema for core and fairness metric thresholds."""

    core_metrics: Dict[str, MetricThreshold]
    fairness_metrics: Dict[str, MetricThreshold]


class PrivacyConfig(BaseModel):
    """Schema controlling privacy safeguards."""

    enable_pii_scrubbing: bool = True
    allowed_pii_patterns: list[str] = Field(default_factory=list)
    blocked_pii_patterns: list[str] = Field(default_factory=list)


class MonitoringConfig(BaseModel):
    """Schema for monitoring guardrails."""

    drift_detection_window: PositiveInt
    alert_threshold: float = Field(gt=0.0)
    latency_budget_ms: PositiveInt


class FairnessGovernanceConfig(BaseModel):
    """Schema describing fairness governance rules."""

    enforce: bool
    sensitive_attributes: list[str] = Field(min_length=1)
    min_samples_per_group: PositiveInt


class ComplianceConfig(BaseModel):
    """Schema for compliance artefact storage."""

    model_config = ConfigDict(protected_namespaces=())
    audit_log_dir: Path
    model_card_dir: Path


class GovernanceConfig(BaseModel):
    """Aggregate governance configuration."""

    privacy: PrivacyConfig
    monitoring: MonitoringConfig
    fairness: FairnessGovernanceConfig
    compliance: ComplianceConfig


class PipelineConfig(BaseModel):
    """Top-level configuration for training and inference."""

    training: TrainingConfig
    inference: InferenceConfig


ConfigModel = TypeVar("ConfigModel", bound=BaseModel)


# SECTION 4: Core Logic / Implementation


def load_yaml(path: Path) -> Mapping[str, Any]:
    """Load and parse a YAML file into a mapping."""

    if not path.exists():
        msg = f"Configuration file not found: {path}"
        raise ConfigValidationError(msg)
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    if not isinstance(data, MutableMapping):
        msg = f"Configuration file {path} did not contain a mapping"
        raise ConfigValidationError(msg)
    return data


def load_config(path: Path, model: Type[ConfigModel]) -> ConfigModel:
    """Load a YAML file and validate it against the provided Pydantic model."""

    raw = load_yaml(path)
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc


# SECTION 5: Error & Edge Case Handling
# - Missing files raise ConfigValidationError early.
# - Non-mapping YAML structures raise ConfigValidationError.
# - Validation errors are wrapped in ConfigValidationError for clarity.


# SECTION 6: Performance Considerations
# - YAML files are loaded once per call; callers should cache results if needed.
# - Validation is performed via Pydantic for speed and clarity.


# SECTION 7: Exports / Public API
__all__ = [
    "ComplianceConfig",
    "ConfigValidationError",
    "DatasetConfig",
    "ExperimentConfig",
    "FairnessGovernanceConfig",
    "GovernanceConfig",
    "InferenceConfig",
    "load_config",
    "load_yaml",
    "MetricsConfig",
    "ModelConfig",
    "ModelHyperparameters",
    "MonitoringConfig",
    "PipelineConfig",
    "PrivacyConfig",
    "TrainingConfig",
]
