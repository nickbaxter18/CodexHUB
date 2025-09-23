"""
SECTION 1: Header & Purpose
- Provides convenient imports for shared configuration schemas and helpers.
- Used by training, inference, and governance layers.
"""

# SECTION 2: Imports / Dependencies
from .config_loader import (
    ComplianceConfig,
    ConfigValidationError,
    DatasetConfig,
    ExperimentConfig,
    FairnessGovernanceConfig,
    GovernanceConfig,
    InferenceConfig,
    MetricsConfig,
    ModelConfig,
    ModelHyperparameters,
    MonitoringConfig,
    PipelineConfig,
    PrivacyConfig,
    TrainingConfig,
    load_config,
    load_yaml,
)

# SECTION 3: Types / Interfaces / Schemas
# - Exposes configuration schema classes for reuse across modules.

# SECTION 4: Core Logic / Implementation
# - No additional logic; this module purely re-exports configuration utilities.

# SECTION 5: Error & Edge Handling
# - Exceptions propagate from the underlying config_loader module.

# SECTION 6: Performance Considerations
# - Minimal import overhead to keep configuration lookups lightweight.

# SECTION 7: Exports / Public API
__all__ = [
    "ComplianceConfig",
    "ConfigValidationError",
    "DatasetConfig",
    "ExperimentConfig",
    "FairnessGovernanceConfig",
    "GovernanceConfig",
    "InferenceConfig",
    "MetricsConfig",
    "ModelConfig",
    "ModelHyperparameters",
    "MonitoringConfig",
    "PipelineConfig",
    "PrivacyConfig",
    "TrainingConfig",
    "load_config",
    "load_yaml",
]
