"""Logging utilities for the runner."""

import logging
from typing import Optional

_LOGGER: Optional[logging.Logger] = None


def get_logger(name: str = "runner") -> logging.Logger:
    """Return a configured logger instance."""

    global _LOGGER
    if _LOGGER is None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        )
        _LOGGER = logging.getLogger("runner")
    return _LOGGER.getChild(name)
