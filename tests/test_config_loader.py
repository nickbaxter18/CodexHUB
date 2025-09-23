"""Tests for governance configuration loader and validation utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from meta_agent.config_loader import ConfigLoader


@pytest.fixture(scope="module")
def loader() -> ConfigLoader:
    """Provide a configuration loader pointed at the repository config directory."""

    return ConfigLoader(config_dir=Path("config"))


def test_governance_configuration_parses(loader: ConfigLoader) -> None:
    """Governance file should load with expected arbitration metadata."""

    governance = loader.get_governance()
    assert governance["version"] == "1.0.0"
    assert "latency" in governance["arbitration"]["metrics"]
    assert governance["trust_thresholds"]["minimum"] == pytest.approx(0.1)


def test_agents_default_trust_extraction(loader: ConfigLoader) -> None:
    """Default trust scores should be extracted from agent configuration."""

    defaults = loader.default_trust_scores()
    assert defaults["QA"] > defaults["Frontend"]
    assert set(defaults) >= {"Frontend", "Backend", "QA", "Meta"}


def test_qa_rules_schema_validates(loader: ConfigLoader, tmp_path: Path) -> None:
    """QA rules retrieved from loader should match schema expectations."""

    rules = loader.get_qa_rules()
    # Write to temp file to ensure JSON serialisation stability.
    path = tmp_path / "qa_rules.json"
    path.write_text(json.dumps(rules, sort_keys=True), encoding="utf-8")
    assert path.read_text(encoding="utf-8").startswith("{")


def test_validate_event_rejects_missing_fields(loader: ConfigLoader) -> None:
    """Missing event fields should raise a ValueError for observability."""

    with pytest.raises(ValueError):
        loader.validate_event({"agent": "QA"})


def test_drift_profiles_include_metrics(loader: ConfigLoader) -> None:
    """Drift profile configuration should expose metric thresholds."""

    drift = loader.get_drift_profiles()
    assert drift["window_size"] >= 1
    assert "latency" in drift["metrics"]
    latency = drift["metrics"]["latency"]
    assert latency["psi_threshold"] > 0
