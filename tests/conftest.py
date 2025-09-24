"""
SECTION: Header & Purpose
    - Pytest configuration ensuring the project root is importable during test execution.

SECTION: Imports / Dependencies
    - Relies on ``pathlib`` and ``sys`` from the standard library.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
