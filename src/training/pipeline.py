"""End-to-end training pipeline aligning documentation with shipped code."""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Mapping, Optional

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.common.config_loader import GovernanceConfig, MetricsConfig, PipelineConfig, load_config
from src.governance.fairness import FairnessMetricResult, evaluate_fairness
from src.performance.metrics_collector import PerformanceCollector, get_performance_collector
from src.registry.registry import MLflowRegistry
from src.training.data_loader import DatasetSplits, load_dataset, split_dataset
from src.training.metrics import MetricResult, compute_classification_metrics, evaluate_thresholds


@dataclass(frozen=True)
class TrainingOutcome:
    """Summary artefacts emitted by a pipeline execution."""

    metrics: Dict[str, float]
    metric_results: Dict[str, MetricResult]
    fairness_results: Dict[str, FairnessMetricResult]
    run_id: Optional[str]


@dataclass(frozen=True)
class _EvaluationResult:
    metrics: Dict[str, float]
    metric_results: Dict[str, MetricResult]
    predictions: np.ndarray


class TrainingPipeline:
    """High-level orchestrator for CodexHUB model training flows."""

    def __init__(
        self,
        pipeline_config_path: Path | str = Path("config/default.yaml"),
        metrics_config_path: Path | str = Path("config/metrics.yaml"),
        governance_config_path: Path | str = Path("config/governance.yaml"),
        *,
        collector: PerformanceCollector | None = None,
        registry_factory: Callable[[PipelineConfig], MLflowRegistry] | None = None,
    ) -> None:
        self._pipeline_config_path = Path(pipeline_config_path)
        self._metrics_config_path = Path(metrics_config_path)
        self._governance_config_path = Path(governance_config_path)
        self._collector = collector or get_performance_collector()
        self._registry_factory = registry_factory

    def run(
        self,
        *,
        pipeline_config: PipelineConfig | None = None,
        metrics_config: MetricsConfig | None = None,
        governance_config: GovernanceConfig | None = None,
    ) -> TrainingOutcome:
        """Execute the pipeline defined in configuration files."""

        config = pipeline_config or load_config(self._pipeline_config_path, PipelineConfig)
        metrics_cfg = metrics_config or load_config(self._metrics_config_path, MetricsConfig)
        governance_cfg = governance_config or load_config(
            self._governance_config_path, GovernanceConfig
        )

        dataset_start = time.perf_counter()
        dataset = load_dataset(config.training.dataset)
        dataset_duration = time.perf_counter() - dataset_start
        self._collector.record_metric(
            "dataset_load_duration",
            dataset_duration,
            category="training",
            metadata={"rows": float(len(dataset))},
        )

        split_start = time.perf_counter()
        splits = split_dataset(config.training.dataset, dataset)
        split_duration = time.perf_counter() - split_start
        self._collector.record_metric("dataset_split_duration", split_duration, category="training")

        model_start = time.perf_counter()
        model = self._train_model(config, splits)
        model_duration = time.perf_counter() - model_start
        self._collector.record_metric("model_train_duration", model_duration, category="training")

        evaluate_start = time.perf_counter()
        evaluation = self._evaluate_metrics(splits, model, metrics_cfg)
        evaluate_duration = time.perf_counter() - evaluate_start
        self._collector.record_metric("model_eval_duration", evaluate_duration, category="training")

        fairness_start = time.perf_counter()
        fairness_results = self._evaluate_fairness(
            splits,
            evaluation.predictions,
            metrics_cfg,
            governance_cfg,
        )
        fairness_duration = time.perf_counter() - fairness_start
        self._collector.record_metric(
            "fairness_eval_duration", fairness_duration, category="training"
        )
        for name, result in fairness_results.items():
            self._collector.record_metric(
                f"fairness_{name}",
                result.value,
                category="fairness",
            )

        run_id = self._log_to_registry(config, evaluation.metrics, fairness_results, model)

        return TrainingOutcome(
            metrics=evaluation.metrics,
            metric_results=evaluation.metric_results,
            fairness_results=fairness_results,
            run_id=run_id,
        )

    def _train_model(self, config: PipelineConfig, splits: DatasetSplits) -> LogisticRegression:
        """Train a baseline logistic regression classifier."""

        hyperparams = config.training.model.hyperparameters
        classifier = LogisticRegression(
            max_iter=hyperparams.epochs,
            solver="lbfgs",
        )
        classifier.fit(splits.x_train, np.asarray(splits.y_train))
        return classifier

    def _evaluate_metrics(
        self,
        splits: DatasetSplits,
        model: LogisticRegression,
        metrics_cfg: MetricsConfig,
    ) -> _EvaluationResult:
        probabilities = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(splits.x_validation)
            probabilities = proba[:, 1]
        predictions = model.predict(splits.x_validation)
        metrics = compute_classification_metrics(
            splits.y_validation,
            predictions,
            probabilities,
        )
        metric_results = evaluate_thresholds(metrics, metrics_cfg)
        return _EvaluationResult(
            metrics=metrics,
            metric_results=metric_results,
            predictions=np.asarray(predictions),
        )

    def _evaluate_fairness(
        self,
        splits: DatasetSplits,
        predictions: np.ndarray,
        metrics_cfg: MetricsConfig,
        governance_cfg: GovernanceConfig,
    ) -> Dict[str, FairnessMetricResult]:
        sensitive_validation = splits.sensitive_validation
        if sensitive_validation is None:
            return {}

        fairness_cfg = governance_cfg.fairness
        column_name = sensitive_validation.name or ""
        expected_attributes = {str(attr) for attr in fairness_cfg.sensitive_attributes}
        if expected_attributes and column_name not in expected_attributes:
            return {}

        return evaluate_fairness(
            splits.y_validation,
            predictions,
            sensitive_validation,
            metrics_cfg,
            fairness_cfg,
        )

    def _log_to_registry(
        self,
        config: PipelineConfig,
        metrics: Mapping[str, float],
        fairness_results: Mapping[str, FairnessMetricResult],
        model: LogisticRegression,
    ) -> Optional[str]:
        if self._registry_factory is None:
            return None

        registry = self._registry_factory(config)
        fairness_metrics = {
            f"fairness_{name}": result.value for name, result in fairness_results.items()
        }
        params = {
            "model_class": type(model).__name__,
            "framework": config.training.model.framework,
            "epochs": config.training.model.hyperparameters.epochs,
            "learning_rate": config.training.model.hyperparameters.learning_rate,
            "batch_size": config.training.model.hyperparameters.batch_size,
        }

        with contextlib.ExitStack() as stack:
            run = stack.enter_context(
                registry.start_run(run_name=config.training.experiment.run_name)
            )
            registry.log_params(run.info.run_id, params)
            registry.log_metrics(run.info.run_id, {**metrics, **fairness_metrics})
            return run.info.run_id


def main(argv: Iterable[str] | None = None) -> int:
    """Command-line entry point supporting ``python -m src.training.pipeline``."""

    pipeline = TrainingPipeline()
    outcome = pipeline.run()
    print("Training metrics:")
    for name, value in outcome.metrics.items():
        print(f"  {name}: {value:.4f}")
    if outcome.fairness_results:
        print("Fairness metrics:")
        for name, result in outcome.fairness_results.items():
            status = "passed" if result.passed else "failed"
            print(f"  {name}: {result.value:.4f} ({status})")
    if outcome.run_id:
        print(f"MLflow run recorded: {outcome.run_id}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI integration point
    raise SystemExit(main())
