from __future__ import annotations

from pathlib import Path

from src.common.config_loader import GovernanceConfig, MetricsConfig, PipelineConfig, load_config
from src.performance.metrics_collector import PerformanceCollector
from src.training.pipeline import TrainingPipeline


def test_training_pipeline_executes(tmp_path: Path) -> None:
    pipeline_config = load_config(Path("config/default.yaml"), PipelineConfig)
    metrics_config = load_config(Path("config/metrics.yaml"), MetricsConfig)
    governance_config = load_config(Path("config/governance.yaml"), GovernanceConfig)

    collector = PerformanceCollector(tmp_path / "metrics")
    pipeline = TrainingPipeline(
        collector=collector,
        registry_factory=None,
    )

    outcome = pipeline.run(
        pipeline_config=pipeline_config,
        metrics_config=metrics_config,
        governance_config=governance_config,
    )

    assert outcome.metrics
    assert "accuracy" in outcome.metric_results
    assert outcome.fairness_results
    assert outcome.run_id is None

    metrics_file = collector.save_metrics()
    assert metrics_file.exists()
