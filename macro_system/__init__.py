"""Compatibility shim for the relocated ``macro_system`` package."""

from __future__ import annotations

import importlib
import sys

_module = importlib.import_module("packages.automation.macro_system")

# Mirror the underlying package so ``import macro_system`` and its submodules continue to work.
sys.modules[__name__] = _module

if hasattr(_module, "__all__"):
    __all__ = list(_module.__all__)  # type: ignore[assignment]
