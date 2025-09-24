"""Unit tests for inference metrics collection and exposure."""

from __future__ import annotations

import math
from typing import Dict, List, cast

import pandas as pd
import pytest

from src.common.config_loader import InferenceConfig
from src.inference import (
    InferenceMetricsCollector,
    InferenceService,
    PredictionResponse,
)
from src.registry.registry import MLflowRegistry


class _DummyModel:
    """Simple model that echoes the sum of values."""

    def predict(self, frame: pd.DataFrame) -> List[float]:  # pragma: no cover - delegated to pandas
        return cast(List[float], frame.sum(axis=1).tolist())


class _DummyRegistry:
    """In-memory registry stub that serves a static model."""

    def __init__(self) -> None:
        self.latest_requested: List[str] = []
        self._model = _DummyModel()

    def latest_model_uri(self, model_name: str) -> str:
        self.latest_requested.append(model_name)
        return f"runs:/{model_name}/1"

    def load_model(self, model_uri: str) -> _DummyModel:
        return self._model


@pytest.fixture()
def inference_config() -> InferenceConfig:
    return InferenceConfig(
        default_model_name="test-model",
        cache_ttl_seconds=60,
        max_batch_size=10,
        concurrency_limit=2,
    )


@pytest.fixture()
def registry() -> _DummyRegistry:
    return _DummyRegistry()


def test_metrics_collector_rejects_invalid_inputs() -> None:
    collector = InferenceMetricsCollector()
    with pytest.raises(ValueError):
        collector.record_prediction(latency_seconds=-1.0, cache_hit=False, record_count=1)
    with pytest.raises(ValueError):
        collector.record_prediction(latency_seconds=0.0, cache_hit=False, record_count=-5)


def test_inference_service_records_metrics(
    inference_config: InferenceConfig, registry: _DummyRegistry
) -> None:
    collector = InferenceMetricsCollector()
    service = InferenceService(
        inference_config,
        cast(MLflowRegistry, registry),
        metrics_collector=collector,
    )

    payload: Dict[str, List[Dict[str, float]]] = {"records": [{"feature": 1.0}, {"feature": 2.0}]}

    response = service.predict(payload)
    assert isinstance(response, PredictionResponse)
    snapshot = service.metrics_snapshot()
    assert snapshot.total_predictions == 1
    assert snapshot.cache_hits == 0
    assert snapshot.cache_misses == 1
    assert snapshot.records_processed == 2
    assert math.isclose(
        snapshot.total_latency_seconds, snapshot.average_latency_seconds, rel_tol=1e-6
    )

    # Second invocation should hit the cache.
    response_again = service.predict(payload)
    assert isinstance(response_again, PredictionResponse)
    snapshot_again = service.metrics_snapshot()
    assert snapshot_again.total_predictions == 2
    assert snapshot_again.cache_hits == 1
    assert snapshot_again.cache_misses == 1
    assert snapshot_again.records_processed == 4
    assert snapshot_again.max_latency_seconds >= snapshot.total_latency_seconds
    assert snapshot_again.last_prediction_timestamp is not None
