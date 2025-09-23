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


# SECTION 4: Core Logic / Implementation


class InferenceService:
    """Inference service with model caching and concurrency controls."""

    def __init__(self, config: InferenceConfig, registry: MLflowRegistry) -> None:
        self._config = config
        self._registry = registry
        self._cache: Dict[str, CachedModel] = {}
        self._cache_lock = Lock()
        self._semaphore = BoundedSemaphore(config.concurrency_limit)

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

        with self._semaphore:
            model, model_uri = self._resolve_model(target_model)
            frame = pd.DataFrame(request.records)
            predictions = model.predict(frame)

        return PredictionResponse(
            predictions=[float(value) for value in predictions],
            model_uri=model_uri,
        )

    def _resolve_model(self, model_name: str) -> tuple[Any, str]:
        with self._cache_lock:
            cached = self._cache.get(model_name)
            now = time.monotonic()
            if cached and cached.expires_at > now:
                return cached.model, cached.model_uri

        model_uri = self._registry.latest_model_uri(model_name)
        model = self._registry.load_model(model_uri)
        expiry = time.monotonic() + self._config.cache_ttl_seconds
        with self._cache_lock:
            self._cache[model_name] = CachedModel(
                model_uri=model_uri, model=model, expires_at=expiry
            )
        return model, model_uri


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
    "InferenceService",
    "PredictionRequest",
    "PredictionResponse",
]
