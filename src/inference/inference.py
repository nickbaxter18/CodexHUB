"""
SECTION 1: Header & Purpose
- Canonical inference logic leveraging the MLflow registry with caching and validation.
- Supplies reusable services for API layers and monitoring pipelines.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
import time
from dataclasses import dataclass
from threading import BoundedSemaphore, Lock
from typing import Any, Dict, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.common.config_loader import InferenceConfig
from src.registry.registry import MLflowRegistry

# SECTION 3: Types / Interfaces / Schemas


class InferenceError(RuntimeError):
    """Raised when inference execution fails."""


class PredictionRequest(BaseModel):
    """Schema defining the expected inference payload."""

    records: list[Dict[str, float]] = Field(min_length=1)


class PredictionResponse(BaseModel):
    """Schema describing the inference response."""

    model_config = ConfigDict(protected_namespaces=())
    predictions: list[float]
    model_uri: str


@dataclass
class CachedModel:
    """Container storing cached model instances."""

    model_uri: str
    model: Any
    expires_at: float


@dataclass(frozen=True)
class InferenceMetricsSnapshot:
    """Immutable snapshot of inference performance metrics."""

    total_predictions: int
    cache_hits: int
    cache_misses: int
    total_latency_seconds: float
    average_latency_seconds: float
    max_latency_seconds: float
    records_processed: int
    last_prediction_timestamp: float | None


class InferenceMetricsCollector:
    """Thread-safe collector tracking inference throughput and latency."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._total_predictions = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_latency = 0.0
        self._max_latency = 0.0
        self._records_processed = 0
        self._last_prediction: float | None = None

    def record_prediction(
        self, *, latency_seconds: float, cache_hit: bool, record_count: int
    ) -> None:
        """Record a completed prediction invocation."""

        if latency_seconds < 0:
            raise ValueError("latency_seconds must be non-negative")
        if record_count < 0:
            raise ValueError("record_count must be non-negative")
        with self._lock:
            self._total_predictions += 1
            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
            self._total_latency += latency_seconds
            if latency_seconds > self._max_latency:
                self._max_latency = latency_seconds
            self._records_processed += record_count
            self._last_prediction = time.monotonic()

    def snapshot(self) -> InferenceMetricsSnapshot:
        """Return a read-only snapshot of collected metrics."""

        with self._lock:
            average_latency = (
                self._total_latency / self._total_predictions if self._total_predictions else 0.0
            )
            return InferenceMetricsSnapshot(
                total_predictions=self._total_predictions,
                cache_hits=self._cache_hits,
                cache_misses=self._cache_misses,
                total_latency_seconds=self._total_latency,
                average_latency_seconds=average_latency,
                max_latency_seconds=self._max_latency,
                records_processed=self._records_processed,
                last_prediction_timestamp=self._last_prediction,
            )


# SECTION 4: Core Logic / Implementation


class InferenceService:
    """Inference service with model caching and concurrency controls."""

    def __init__(
        self,
        config: InferenceConfig,
        registry: MLflowRegistry,
        *,
        metrics_collector: InferenceMetricsCollector | None = None,
    ) -> None:
        self._config = config
        self._registry = registry
        self._cache: Dict[str, CachedModel] = {}
        self._cache_lock = Lock()
        self._semaphore = BoundedSemaphore(config.concurrency_limit)
        self._metrics = metrics_collector or InferenceMetricsCollector()

    def predict(
        self, payload: Dict[str, Any], model_name: Optional[str] = None
    ) -> PredictionResponse:
        try:
            request = PredictionRequest.model_validate(payload)
        except ValidationError as exc:
            raise InferenceError(str(exc)) from exc

        if len(request.records) > self._config.max_batch_size:
            raise InferenceError("Batch size exceeds configured maximum")

        target_model = model_name or self._config.default_model_name
        start_time = time.perf_counter()

        with self._semaphore:
            model, model_uri, cache_hit = self._resolve_model(target_model)
            frame = pd.DataFrame(request.records)
            predictions = model.predict(frame)

        latency = time.perf_counter() - start_time
        self._metrics.record_prediction(
            latency_seconds=latency,
            cache_hit=cache_hit,
            record_count=len(request.records),
        )

        return PredictionResponse(
            predictions=[float(value) for value in predictions],
            model_uri=model_uri,
        )

    def metrics_snapshot(self) -> InferenceMetricsSnapshot:
        """Expose a snapshot of inference performance metrics."""

        return self._metrics.snapshot()

    def _resolve_model(self, model_name: str) -> tuple[Any, str, bool]:
        with self._cache_lock:
            cached = self._cache.get(model_name)
            now = time.monotonic()
            if cached and cached.expires_at > now:
                return cached.model, cached.model_uri, True

        model_uri = self._registry.latest_model_uri(model_name)
        model = self._registry.load_model(model_uri)
        expiry = time.monotonic() + self._config.cache_ttl_seconds
        with self._cache_lock:
            self._cache[model_name] = CachedModel(
                model_uri=model_uri, model=model, expires_at=expiry
            )
        return model, model_uri, False


# SECTION 5: Error & Edge Case Handling
# - Payload validation errors converted into InferenceError for uniform handling.
# - Batch size limits enforced to avoid resource exhaustion.
# - Cache refresh protects against stale models by respecting TTL.


# SECTION 6: Performance Considerations
# - Bounded semaphore enforces concurrency limit to maintain latency budgets.
# - Cached models avoid repeated registry fetches, minimizing load and improving latency.


# SECTION 7: Exports / Public API
__all__ = [
    "CachedModel",
    "InferenceError",
    "InferenceMetricsCollector",
    "InferenceMetricsSnapshot",
    "InferenceService",
    "PredictionRequest",
    "PredictionResponse",
]
