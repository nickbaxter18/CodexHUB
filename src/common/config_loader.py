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
from typing import Any, Dict, Iterable, Literal, Mapping, MutableMapping, Type, TypeVar

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


class LogisticRegressionHyperparameters(BaseModel):
    """Hyperparameters supported by the baseline logistic regression model."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    max_iterations: PositiveInt = Field(default=200, alias="max_iterations")
    solver: str = Field(default="lbfgs")
    penalty: str = Field(default="l2")
    regularization_strength: float = Field(gt=0.0, default=1.0, alias="regularization_strength")

    @field_validator("solver")
    @classmethod
    def _normalize_solver(cls, value: str) -> str:
        normalized = value.lower()
        allowed = {"lbfgs", "liblinear", "newton-cg", "saga", "sag"}
        if normalized not in allowed:
            raise ValueError(f"Unsupported solver '{value}'. Expected one of: {sorted(allowed)}")
        return normalized

    @field_validator("penalty")
    @classmethod
    def _normalize_penalty(cls, value: str) -> str:
        normalized = value.lower()
        allowed = {"l1", "l2", "elasticnet", "none"}
        if normalized not in allowed:
            raise ValueError(f"Unsupported penalty '{value}'. Expected one of: {sorted(allowed)}")
        return normalized

    @model_validator(mode="after")
    def _validate_combination(self) -> "LogisticRegressionHyperparameters":
        if self.penalty == "l1" and self.solver not in {"liblinear", "saga"}:
            raise ValueError("l1 penalty requires either 'liblinear' or 'saga' solver")
        if self.penalty == "elasticnet" and self.solver != "saga":
            raise ValueError("elasticnet penalty requires the 'saga' solver")
        if self.penalty == "none" and self.solver not in {"lbfgs", "newton-cg", "sag"}:
            raise ValueError(
                "penalty 'none' is only supported with lbfgs, newton-cg, or sag solvers"
            )
        return self


class ModelConfig(BaseModel):
    """Schema describing model metadata and hyperparameters."""

    framework: Literal["sklearn-logistic-regression"]
    hyperparameters: LogisticRegressionHyperparameters


# Backwards compatibility alias for downstream imports that still reference ModelHyperparameters.
ModelHyperparameters = LogisticRegressionHyperparameters


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


class EnvironmentSettings(BaseModel):
    """Schema describing required environment variables for CodexHUB."""

    model_config = ConfigDict(populate_by_name=True, extra="allow", protected_namespaces=())

    port: PositiveInt = Field(alias="PORT", default=4000)
    node_env: Literal["development", "production", "test"] = Field(
        alias="NODE_ENV",
        default="development",
    )
    session_secret: str = Field(
        alias="SESSION_SECRET",
        default="replace-with-strong-secret",
    )
    openai_api_key: str = Field(alias="OPENAI_API_KEY", default="changeme")
    cursor_api_key: str | None = Field(alias="CURSOR_API_KEY", default=None)
    cursor_api_url: str = Field(alias="CURSOR_API_URL", default="https://api.cursor.sh")
    mlflow_tracking_uri: str = Field(
        alias="MLFLOW_TRACKING_URI",
        default="./results/mlruns",
    )
    mlflow_registry_uri: str = Field(
        alias="MLFLOW_REGISTRY_URI",
        default="./results/mlruns",
    )
    mlflow_experiment_name: str = Field(
        alias="MLFLOW_EXPERIMENT_NAME",
        default="CodexHUB-Baseline",
    )
    pipeline_config_path: Path = Field(
        alias="PIPELINE_CONFIG_PATH",
        default=Path("config/default.yaml"),
    )
    governance_config_path: Path = Field(
        alias="GOVERNANCE_CONFIG_PATH",
        default=Path("config/governance.yaml"),
    )
    metrics_config_path: Path = Field(
        alias="METRICS_CONFIG_PATH",
        default=Path("config/metrics.yaml"),
    )
    performance_results_dir: Path = Field(
        alias="PERFORMANCE_RESULTS_DIR",
        default=Path("results/performance"),
    )
    audit_log_dir: Path = Field(
        alias="AUDIT_LOG_DIR",
        default=Path("results/audit"),
    )
    model_card_dir: Path = Field(
        alias="MODEL_CARD_DIR",
        default=Path("docs/model_cards"),
    )
    cursor_auto_invocation_enabled: bool = Field(
        alias="CURSOR_AUTO_INVOCATION_ENABLED",
        default=False,
    )
    cursor_monitor_interval: PositiveInt = Field(alias="CURSOR_MONITOR_INTERVAL", default=5)
    cursor_file_patterns: str = Field(
        alias="CURSOR_FILE_PATTERNS",
        default="**/*.tsx,**/*.py,**/*.md,**/*.js,**/*.ts",
    )
    knowledge_auto_load: bool = Field(alias="KNOWLEDGE_AUTO_LOAD", default=False)
    knowledge_ndjson_paths: str | None = Field(
        alias="KNOWLEDGE_NDJSON_PATHS",
        default="Brain docs cleansed .ndjson,Bundle cleansed .ndjson",
    )
    knowledge_watch_interval: PositiveInt | None = Field(
        alias="KNOWLEDGE_WATCH_INTERVAL",
        default=None,
    )
    mobile_control_enabled: bool = Field(alias="MOBILE_CONTROL_ENABLED", default=False)
    mobile_notifications_enabled: bool = Field(alias="MOBILE_NOTIFICATIONS_ENABLED", default=False)
    mobile_app_port: PositiveInt = Field(alias="MOBILE_APP_PORT", default=3001)
    brain_blocks_auto_load: bool = Field(alias="BRAIN_BLOCKS_AUTO_LOAD", default=False)
    brain_blocks_data_source: str = Field(
        alias="BRAIN_BLOCKS_DATA_SOURCE",
        default="Brain docs cleansed .ndjson",
    )
    brain_blocks_query_depth: str = Field(alias="BRAIN_BLOCKS_QUERY_DEPTH", default="summary")
    cursor_performance_monitoring: bool = Field(
        alias="CURSOR_PERFORMANCE_MONITORING",
        default=False,
    )
    cursor_usage_tracking: bool = Field(alias="CURSOR_USAGE_TRACKING", default=False)
    cursor_compliance_reporting: bool = Field(alias="CURSOR_COMPLIANCE_REPORTING", default=False)

    @staticmethod
    def _parse_bool(value: bool | str | None, *, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
        msg = f"Unable to interpret boolean value from '{value}'"
        raise ValueError(msg)

    @field_validator(
        "cursor_auto_invocation_enabled",
        "knowledge_auto_load",
        "mobile_control_enabled",
        "mobile_notifications_enabled",
        "brain_blocks_auto_load",
        "cursor_performance_monitoring",
        "cursor_usage_tracking",
        "cursor_compliance_reporting",
        mode="before",
    )
    @classmethod
    def _validate_bool_fields(cls, value: bool | str | None) -> bool:
        return cls._parse_bool(value)

    @field_validator("knowledge_ndjson_paths", "cursor_file_patterns", mode="before")
    @classmethod
    def _strip_quotes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if (trimmed.startswith('"') and trimmed.endswith('"')) or (
            trimmed.startswith("'") and trimmed.endswith("'")
        ):
            return trimmed[1:-1]
        return value

    @field_validator(
        "cursor_monitor_interval",
        "mobile_app_port",
        "knowledge_watch_interval",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, value: str | int | None) -> int | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


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


def _parse_env_file(path: Path) -> Dict[str, Any]:
    """Parse a dotenv-style file into a mapping."""

    if not path.exists():
        raise ConfigValidationError(f"Environment file not found: {path}")

    data: Dict[str, Any] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                msg = f"Invalid environment entry on line {line_number}: {raw_line.rstrip()}"
                raise ConfigValidationError(msg)
            key, raw_value = line.split("=", 1)
            value = raw_value.strip()
            if value in {"", "''", '""'}:
                parsed_value: Any = None
            else:
                parsed_value = value
            data[key.strip()] = parsed_value
    return data


def load_environment(path: Path) -> EnvironmentSettings:
    """Load and validate environment variables from a dotenv file."""

    try:
        raw = _parse_env_file(path)
    except OSError as exc:  # pragma: no cover - filesystem errors
        raise ConfigValidationError(str(exc)) from exc

    try:
        return EnvironmentSettings.model_validate(raw)
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


def validate_environment_files(paths: Iterable[Path]) -> Dict[str, Any]:
    """Validate environment files and return structured results."""

    results: Dict[str, Any] = {}
    for env_path in paths:
        key = f"env::{env_path}"
        try:
            instance = load_environment(env_path)
        except ConfigValidationError as exc:
            results[key] = {
                "status": "error",
                "path": str(env_path),
                "message": str(exc),
            }
            continue

        results[key] = {
            "status": "ok",
            "path": str(env_path),
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
    parser.add_argument(
        "--env",
        action="append",
        type=Path,
        default=[],
        help="Validate one or more environment files against the repository schema.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    config_map = _default_config_map(args.project_root)
    results = validate_known_configs(config_map)

    if args.env:
        env_results = validate_environment_files(args.env)
        results.update(env_results)

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
    "EnvironmentSettings",
    "ExperimentConfig",
    "FairnessGovernanceConfig",
    "GovernanceConfig",
    "load_environment",
    "InferenceConfig",
    "load_config",
    "load_yaml",
    "MetricsConfig",
    "ModelConfig",
    "LogisticRegressionHyperparameters",
    "ModelHyperparameters",
    "MonitoringConfig",
    "PipelineConfig",
    "PrivacyConfig",
    "validate_environment_files",
    "TrainingConfig",
]
