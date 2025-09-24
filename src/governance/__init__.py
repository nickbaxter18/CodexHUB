"""
SECTION 1: Header & Purpose
- Aggregates governance utilities for fairness and privacy enforcement.
- Simplifies import paths for governance-aware workflows.
"""

# SECTION 2: Imports / Dependencies
from .fairness import FairnessMetricResult, evaluate_fairness
from .policy_enforcer import PolicyDecision, PolicyEnforcementResult, PolicyEnforcer
from .privacy import PIIScrubbingError, contains_blocked_pii, scrub_text

# SECTION 3: Types / Interfaces / Schemas
# - Re-exports fairness and privacy result structures.

# SECTION 4: Core Logic / Implementation
# - No additional logic; this namespace consolidates governance utilities.

# SECTION 5: Error & Edge Handling
# - Exceptions bubble from the underlying modules to the caller.

# SECTION 6: Performance Considerations
# - Import-time work is minimal, ensuring lightweight governance checks.

# SECTION 7: Exports / Public API
__all__ = [
    "FairnessMetricResult",
    "PIIScrubbingError",
    "PolicyDecision",
    "PolicyEnforcementResult",
    "PolicyEnforcer",
    "contains_blocked_pii",
    "evaluate_fairness",
    "scrub_text",
]
