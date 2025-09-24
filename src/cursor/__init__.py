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

__version__ = "4.3.0"
__author__ = "U-DIG IT Meta-Intelligence System"

__all__ = [
    "CursorClient",
    "CursorConfig", 
    "CursorAPIError",
    "AgentType",
    "RequestType",
    "RequestPayload",
    "VisualRefinementCursor",
    "create_cursor_client"
]
