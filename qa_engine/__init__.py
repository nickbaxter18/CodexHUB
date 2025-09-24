"""Compatibility shim for the relocated ``qa_engine`` package."""

from __future__ import annotations

import importlib
import sys

_module = importlib.import_module("packages.automation.qa_engine")
sys.modules[__name__] = _module

if hasattr(_module, "__all__"):
    __all__ = list(_module.__all__)  # type: ignore[assignment]
