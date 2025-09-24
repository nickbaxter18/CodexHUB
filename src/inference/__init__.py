"""
SECTION 1: Header & Purpose
- Provides import shortcuts for inference services and schemas.
- Used by API layers and offline batch jobs.
"""

# SECTION 2: Imports / Dependencies
from .inference import (
    CachedModel,
    InferenceError,
    InferenceMetricsCollector,
    InferenceMetricsSnapshot,
    InferenceService,
    PredictionRequest,
    PredictionResponse,
)

# SECTION 3: Types / Interfaces / Schemas
# - Re-exports prediction schemas for consistent validation.

# SECTION 4: Core Logic / Implementation
# - Pure re-export module.

# SECTION 5: Error & Edge Handling
# - Exceptions bubble from underlying inference module.

# SECTION 6: Performance Considerations
# - Minimal overhead; does not instantiate services automatically.

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
