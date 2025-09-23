"""Structured logging helper utilities for the MetaAgent orchestration stack."""

# === Header & Purpose ===
# The logger centralises JSON-formatted diagnostic output for arbitration,
# trust adjustments, and drift detections so that human operators and CI agents
# have a consistent telemetry stream.

# === Imports / Dependencies ===
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class Logger:
    """Emit structured JSON log entries to stdout and rotating files."""

    def __init__(self, log_dir: Path | str = Path("logs"), *, name: str = "meta_agent") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._log_dir / f"{name}.log"
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def _write(self, level: str, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "data": payload or {},
        }
        line = json.dumps(record, sort_keys=True)
        try:
            with self._log_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.write("\n")
        except OSError:
            # Fallback to stderr when file logging fails.
            self._logger.error("Failed to write structured log", extra={"payload": record})
        self._logger.log(getattr(logging, level, logging.INFO), line)

    def info(self, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self._write("INFO", message, payload)

    def warning(self, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self._write("WARNING", message, payload)

    def error(self, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self._write("ERROR", message, payload)

    def debug(self, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self._write("DEBUG", message, payload)


# === Error & Edge Case Handling ===
# File IO failures fall back to stderr logging. Payloads default to empty dicts
# so that callers may pass ``None`` conveniently.


# === Performance Considerations ===
# Logging performs a single file append per entry; for high-throughput
# environments this could be buffered or replaced with asynchronous sinks.


# === Exports / Public API ===
__all__ = ["Logger"]
