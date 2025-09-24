"""API integration service reserved for Stage 2 enhancements."""

from __future__ import annotations

from typing import Dict


def list_plugins() -> Dict[str, str]:
    """Return an empty plugin mapping for Stage 1."""

    return {}
