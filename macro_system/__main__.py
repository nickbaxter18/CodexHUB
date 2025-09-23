"""Header & Purpose: executable entry point delegating to the Macros CLI."""

from __future__ import annotations

# === Imports / Dependencies ===
from typing import Sequence

from .Macros.cli import main as _cli_main

# === Types / Interfaces / Schemas ===
Args = Sequence[str]


# === Core Logic / Implementation ===
def main(argv: Args | None = None) -> int:
    """Invoke the Macros CLI entry point with optional arguments."""

    return _cli_main(argv)


# === Error & Edge Handling ===
# CLI exceptions propagate for upstream handling, mirroring direct CLI usage.


# === Performance Considerations ===
# Simple delegation adds no measurable overhead beyond the CLI invocation.


# === Exports / Public API ===
__all__ = ["main"]


if __name__ == "__main__":  # pragma: no cover - command-line entry
    import sys

    raise SystemExit(main(sys.argv[1:]))
