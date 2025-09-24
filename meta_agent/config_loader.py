"""Config loading utilities for governance-aware meta agent orchestration."""

# === Header & Purpose ===
# This module centralises validation and parsing of governance artefacts such as
# agent registries, arbitration priorities, QA policies, and supporting schemas.
# A single loader prevents divergence between local development and CI by
# ensuring every consumer sees the same validated configuration snapshot.

# === Imports / Dependencies ===
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, cast

from jsonschema import ValidationError, validate


# === Types, Interfaces, Contracts ===
class ConfigLoader:
    """Load governance configuration and validate payloads against schemas."""

    def __init__(self, config_dir: Path | str = Path("config")) -> None:
        self._config_dir = Path(config_dir)
        self._cache: MutableMapping[str, Dict[str, Any]] = {}

    def _load(self, file_name: str, schema_name: str) -> Dict[str, Any]:
        """Read ``file_name`` from disk and validate the JSON payload."""

        path = self._config_dir / file_name
        schema_path = self._config_dir / schema_name
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (
            FileNotFoundError
        ) as exc:  # pragma: no cover - configuration error surfaced to caller
            raise ValueError(f"Config file '{file_name}' is missing") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Config file '{file_name}' is not valid JSON: {exc}") from exc

        try:
            schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
        except (
            FileNotFoundError
        ) as exc:  # pragma: no cover - configuration error surfaced to caller
            raise ValueError(f"Schema file '{schema_name}' is missing") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Schema file '{schema_name}' is not valid JSON: {exc}") from exc

        try:
            validate(payload, schema_data)
        except ValidationError as exc:
            raise ValueError(f"{file_name} failed validation: {exc.message}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"{file_name} payload must be a JSON object")
        return cast(Dict[str, Any], payload)

    def _get_or_load(self, key: str, file_name: str, schema_name: str) -> Dict[str, Any]:
        if key not in self._cache:
            self._cache[key] = self._load(file_name, schema_name)
        return dict(self._cache[key])

    def get_governance(self) -> Dict[str, Any]:
        """Return the validated governance configuration."""

        return self._get_or_load("governance", "governance.json", "governance.schema.json")

    def get_agents(self) -> Dict[str, Any]:
        """Return the registered agents and their metadata."""

        return self._get_or_load("agents", "agents.json", "agents.schema.json")

    def get_qa_policies(self) -> Dict[str, Any]:
        """Return QA policy thresholds for probabilistic evaluation."""

        return self._get_or_load("qa_policies", "qa_policies.json", "qa_policies.schema.json")

    def get_qa_rules(self) -> Dict[str, Any]:
        """Return the QA rules payload for consumers that require direct access."""

        return self._get_or_load("qa_rules", "qa_rules.json", "qa_rules.schema.json")

    def get_drift_profiles(self) -> Dict[str, Any]:
        """Return statistical drift reference profiles and enforcement thresholds."""

        return self._get_or_load("drift", "drift.json", "drift.schema.json")

    def resolve_path(self, name: str) -> Path:
        """Return an absolute path under the configuration directory."""

        return self._config_dir / name

    def validate_event(self, event: Mapping[str, Any]) -> None:
        """Ensure inbound QA events contain the required canonical keys."""

        required = {"agent", "metric", "value", "threshold", "status"}
        missing = sorted(required - set(event))
        if missing:
            raise ValueError(f"Missing required event fields: {', '.join(missing)}")

    def default_trust_scores(self) -> Dict[str, float]:
        """Derive default trust scores from the agents configuration."""

        agents = self.get_agents()
        defaults: Dict[str, float] = {}
        for agent, config in agents.items():
            try:
                defaults[agent] = float(config.get("default_trust", 1.0))
            except (TypeError, ValueError):
                defaults[agent] = 1.0
        return defaults


# === Error & Edge Case Handling ===
# - File-not-found and JSON decode issues surface as ValueError with helpful context.
# - Schema validation errors propagate precise jsonschema messages for rapid debugging.
# - Cache ensures subsequent lookups do not repeat disk IO, while returning copies to
#   avoid accidental mutation of shared state.


# === Performance Considerations ===
# - Config files are small; caching prevents repeated JSON parsing.
# - jsonschema validation is performed once per process invocation.


# === Exports / Public API ===
__all__ = ["ConfigLoader"]
