"""
SECTION 1: Header & Purpose
- Compliance tests verifying PII scrubbing behaviour.
"""

# SECTION 2: Imports / Dependencies

from src.common.config_loader import PrivacyConfig
from src.governance.privacy import contains_blocked_pii, scrub_text

# SECTION 3: Types / Interfaces / Schemas
# - Utilizes PrivacyConfig schema for scrubbing configuration.

# SECTION 4: Core Logic / Implementation


def test_scrub_text_replaces_pii() -> None:
    config = PrivacyConfig(
        enable_pii_scrubbing=True,
        blocked_pii_patterns=["email", "phone"],
        allowed_pii_patterns=[],
    )
    text = "Contact me at sample@example.com or +1-202-555-0198"
    scrubbed = scrub_text(text, config)
    assert "[REDACTED]" in scrubbed
    assert "example.com" not in scrubbed


def test_contains_blocked_pii_with_allowlist() -> None:
    config = PrivacyConfig(
        enable_pii_scrubbing=True,
        blocked_pii_patterns=["email"],
        allowed_pii_patterns=["email"],
    )
    text = "team@codexhub.ai"
    assert not contains_blocked_pii(text, config)


# SECTION 5: Error & Edge Case Handling
# - Ensures allowlist disables scrubbing for permitted patterns.


# SECTION 6: Performance Considerations
# - Operates on short strings; negligible runtime.


# SECTION 7: No exports required for test modules.
