"""
SECTION 1: Header & Purpose
- Provides privacy utilities that detect and scrub personally identifiable information (PII).
- Keeps artefacts and logs compliant with privacy commitments for governance enforcement.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
import re
from typing import Dict, Pattern

from src.common.config_loader import PrivacyConfig

# SECTION 3: Types / Interfaces / Schemas


class PIIScrubbingError(RuntimeError):
    """Raised when PII scrubbing encounters unrecoverable errors."""


# SECTION 4: Core Logic / Implementation

DEFAULT_PATTERNS: Dict[str, Pattern[str]] = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE),
    "phone": re.compile(r"(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}"),
    "ssn": re.compile(r"\d{3}-\d{2}-\d{4}"),
}
REDACTION_TOKEN = "[REDACTED]"


def scrub_text(text: str, config: PrivacyConfig) -> str:
    """Scrub configured PII patterns from text."""

    if not config.enable_pii_scrubbing:
        return text

    patterns = _compile_patterns(config)
    scrubbed = text
    for _name, pattern in patterns.items():
        scrubbed = pattern.sub(REDACTION_TOKEN, scrubbed)
    return scrubbed


def contains_blocked_pii(text: str, config: PrivacyConfig) -> bool:
    """Check if the text contains blocked PII patterns."""

    if not config.enable_pii_scrubbing:
        return False
    patterns = _compile_patterns(config)
    return any(pattern.search(text) for pattern in patterns.values())


# SECTION 5: Error & Edge Case Handling
# - Gracefully exits when scrubbing disabled.
# - Raises PIIScrubbingError when unknown blocked patterns are requested.
# - Supports custom allowlists to bypass specific patterns while retaining security defaults.


# SECTION 6: Performance Considerations
# - Compiles regex patterns once per invocation to balance flexibility with performance.
# - Designed for short text snippets (logs, artefacts).
# - Stream large documents through chunked processors.


# SECTION 7: Exports / Public API
__all__ = ["PIIScrubbingError", "contains_blocked_pii", "scrub_text"]


def _compile_patterns(config: PrivacyConfig) -> Dict[str, Pattern[str]]:
    """Compile regex patterns respecting allow and block lists."""

    patterns: Dict[str, Pattern[str]] = {}
    for name in config.blocked_pii_patterns:
        if name in config.allowed_pii_patterns:
            continue
        if name not in DEFAULT_PATTERNS:
            raise PIIScrubbingError(f"Unsupported PII pattern: {name}")
        patterns[name] = DEFAULT_PATTERNS[name]
    return patterns
