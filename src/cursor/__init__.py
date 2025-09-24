"""
Cursor Client Package for U-DIG IT WebsiteOS Meta-Intelligence v4.3+

This package provides comprehensive Cursor API integration for the Codex system,
enabling intelligent reasoning, generation, refactoring, and summarization.

Author: U-DIG IT Meta-Intelligence System
Version: 4.3+
License: MIT
"""

from .cursor_client import (
    CursorClient,
    CursorConfig,
    CursorAPIError,
    AgentType,
    RequestType,
    RequestPayload,
    VisualRefinementCursor,
    create_cursor_client
)

from .auto_invocation import (
    CursorAutoInvoker,
    AutoInvocationRule,
    get_auto_invoker,
    start_cursor_auto_invocation
)

from .enforcement import (
    CursorEnforcementError,
    enforce_cursor_integration,
    require_cursor_agent,
    validate_cursor_compliance,
    get_cursor_usage_report
)

__version__ = "4.3.0"
__author__ = "U-DIG IT Meta-Intelligence System"

__all__ = [
    # Core Cursor Client
    "CursorClient",
    "CursorConfig", 
    "CursorAPIError",
    "AgentType",
    "RequestType",
    "RequestPayload",
    "VisualRefinementCursor",
    "create_cursor_client",
    
    # Auto-Invocation System
    "CursorAutoInvoker",
    "AutoInvocationRule",
    "get_auto_invoker",
    "start_cursor_auto_invocation",
    
    # Enforcement System
    "CursorEnforcementError",
    "enforce_cursor_integration",
    "require_cursor_agent",
    "validate_cursor_compliance",
    "get_cursor_usage_report"
]
