"""
SECTION 1: Header & Purpose
- Provides shared configuration utilities that load and validate YAML settings.
- Supports training, inference, and governance modules with deterministic, schema-driven defaults.
"""

# SECTION 2: Imports / Dependencies
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Type, TypeVar

import yaml  # type: ignore[import-untyped]
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
    sensitive_attribute: str | None = None

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

    @field_validator("sensitive_attribute")
    @classmethod
    def _normalize_sensitive_attribute(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("sensitive_attribute cannot be blank if provided")
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


def _default_config_map(project_root: Path | None = None) -> Dict[str, Path]:
    root = project_root or Path.cwd()
    return {
        "pipeline": root / "config" / "default.yaml",
        "governance": root / "config" / "governance.yaml",
        "metrics": root / "config" / "metrics.yaml",
    }


def validate_known_configs(config_map: Mapping[str, Path] | None = None) -> Dict[str, Any]:
    """Validate standard configuration bundles and return structured results."""

    results: Dict[str, Any] = {}
    mapping = config_map or _default_config_map()
    for name, path in mapping.items():
        model: Type[BaseModel]
        if name == "pipeline":
            model = PipelineConfig
        elif name == "governance":
            model = GovernanceConfig
        elif name == "metrics":
            model = MetricsConfig
        else:
            results[name] = {"status": "skipped", "path": str(path)}
            continue

        try:
            instance = load_config(path, model)
        except ConfigValidationError as exc:
            results[name] = {
                "status": "error",
                "path": str(path),
                "message": str(exc),
            }
            continue

        results[name] = {
            "status": "ok",
            "path": str(path),
            "model": instance.model_dump(mode="json"),
        }
    return results


def _render_validation_report(results: Mapping[str, Any]) -> str:
    """Render a human-readable validation report."""

    lines: list[str] = ["Configuration Validation Report", "=" * 33]
    for name, payload in results.items():
        status = payload.get("status", "unknown")
        lines.append(f"{name}: {status}")
        message = payload.get("message")
        if message:
            lines.append(f"  error: {message}")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    """Entry-point for ``python -m src.common.config_loader``."""

    parser = argparse.ArgumentParser(description="Validate CodexHUB configuration bundles.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON report instead of human readable text.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Override the project root when resolving config paths.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    config_map = _default_config_map(args.project_root)
    results = validate_known_configs(config_map)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(_render_validation_report(results))

    failures = [name for name, payload in results.items() if payload.get("status") != "ok"]
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())


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
