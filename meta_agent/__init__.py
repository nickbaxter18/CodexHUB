"""Compatibility shim for the relocated ``meta_agent`` package."""

from __future__ import annotations

import importlib
import sys

_module = importlib.import_module("packages.automation.meta_agent")
sys.modules[__name__] = _module

if hasattr(_module, "__all__"):
    __all__ = list(_module.__all__)  # type: ignore[assignment]
