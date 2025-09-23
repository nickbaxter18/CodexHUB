"""
SECTION 1: Header & Purpose
- Exposes MLflow registry integration utilities for the wider pipeline.
- Facilitates tracking and retrieval operations from a single import path.
"""

# SECTION 2: Imports / Dependencies
from .registry import MLflowRegistry, RegistryError

# SECTION 3: Types / Interfaces / Schemas
# - Re-exports MLflowRegistry class for consumer modules.

# SECTION 4: Core Logic / Implementation
# - No runtime logic beyond re-export.

# SECTION 5: Error & Edge Handling
# - Exceptions propagate from the registry module.

# SECTION 6: Performance Considerations
# - Minimal import overhead to preserve CLI responsiveness.

# SECTION 7: Exports / Public API
__all__ = ["MLflowRegistry", "RegistryError"]
