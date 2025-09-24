"""Compatibility layer for legacy agents imports.

This module re-exports the automation agents that now live under
``packages.automation.agents`` so existing import paths continue to work
while the codebase adopts the normalized packages/ layout.
"""

# Re-export the documented public API for introspection tools.
from packages.automation.agents import *  # noqa: F401,F403
from packages.automation.agents import __all__ as _ALL

__all__ = list(_ALL)
