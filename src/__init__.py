"""
SECTION 1: Header & Purpose
- Root Python package initializer for CodexHUB AI governance pipeline modules.
- Exposes high-level namespaces for training, inference, governance, registry, and shared utilities.
"""

# SECTION 2: Imports / Dependencies
from . import common, governance, inference, registry, training

# SECTION 3: Types / Interfaces / Schemas
# - This module re-exports subpackages; no additional schemas defined here.

# SECTION 4: Core Logic / Implementation
# - No runtime logic; serves as namespace aggregator.

# SECTION 5: Error & Edge Handling
# - No runtime behaviour; importing failures bubble from submodules.

# SECTION 6: Performance Considerations
# - Import side-effects are minimal, keeping package import lightweight.

# SECTION 7: Exports / Public API
__all__ = ["common", "governance", "inference", "registry", "training"]
