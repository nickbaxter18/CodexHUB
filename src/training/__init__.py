"""
SECTION 1: Header & Purpose
- Exposes training utilities including dataset loading and metric evaluation.
- Serves as entrypoint for orchestrating CodexHUB training pipelines.
"""

# SECTION 2: Imports / Dependencies
from .data_loader import DatasetSplits, load_dataset, split_dataset
from .metrics import MetricResult, compute_classification_metrics, evaluate_thresholds

# SECTION 3: Types / Interfaces / Schemas
# - Re-exports DatasetSplits and MetricResult for package consumers.

# SECTION 4: Core Logic / Implementation
# - No runtime logic; this module aggregates exports for convenience.

# SECTION 5: Error & Edge Handling
# - Exceptions propagate from submodules directly.

# SECTION 6: Performance Considerations
# - Import-time work kept minimal to ensure fast module loading.

# SECTION 7: Exports / Public API
__all__ = [
    "DatasetSplits",
    "MetricResult",
    "compute_classification_metrics",
    "evaluate_thresholds",
    "load_dataset",
    "split_dataset",
]
