#!/usr/bin/env python3
"""Validate configuration assets (JSON, YAML, env files) against their schemas."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator, FormatChecker, ValidationError


@dataclass(frozen=True)
class JsonSchemaTarget:
    """Pairs a JSON payload with the schema used to validate it."""

    payload: Path
    schema: Path


JSON_SCHEMA_TARGETS: tuple[JsonSchemaTarget, ...] = (
    JsonSchemaTarget(Path("governance.json"), Path("governance.schema.json")),
    JsonSchemaTarget(Path("agents.json"), Path("agents.schema.json")),
    JsonSchemaTarget(Path("qa_policies.json"), Path("qa_policies.schema.json")),
    JsonSchemaTarget(Path("qa_rules.json"), Path("qa_rules.schema.json")),
)

YAML_TARGETS: tuple[str, ...] = (
    "default.yaml",
    "governance.yaml",
    "metrics.yaml",
)

ENV_FILES: tuple[str, ...] = ("cursor.env",)

ENV_DIRS: tuple[str, ...] = ("environments",)

PATH_FORMAT_CHECKER = FormatChecker()


@PATH_FORMAT_CHECKER.checks("path")
def _validate_path_format(value: str) -> bool:
    """Ensure path-like strings are not empty."""

    return isinstance(value, str) and value.strip() != ""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        raise ValueError("YAML file is empty")
    return data


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _coerce_env_value(value: str) -> Any:
    cleaned = _strip_quotes(value.strip())
    if cleaned == "":
        return None
    lowered = cleaned.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(cleaned)
    except ValueError:
        pass
    try:
        return float(cleaned)
    except ValueError:
        pass
    return cleaned


def load_env(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid line (missing '='): {raw_line}")
        key, raw_value = line.split("=", 1)
        values[key.strip()] = _coerce_env_value(raw_value)
    return values


def iter_env_files(config_dir: Path) -> Iterable[Path]:
    for filename in ENV_FILES:
        yield config_dir / filename
    for directory in ENV_DIRS:
        for candidate in sorted((config_dir / directory).glob("*.env")):
            yield candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-dir", default="config", help="Directory containing configuration files"
    )
    parser.add_argument(
        "--env-schema", default="env.schema.json", help="Schema used to validate .env files"
    )
    args = parser.parse_args()

    config_dir = Path(args.config_dir)
    errors: dict[str, str] = {}

    for target in JSON_SCHEMA_TARGETS:
        payload_path = config_dir / target.payload
        schema_path = config_dir / target.schema
        try:
            payload = load_json(payload_path)
            schema = load_json(schema_path)
            Draft7Validator(schema, format_checker=PATH_FORMAT_CHECKER).validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            errors[payload_path.name] = str(exc)

    for yaml_name in YAML_TARGETS:
        yaml_path = config_dir / yaml_name
        try:
            load_yaml(yaml_path)
        except (OSError, yaml.YAMLError, ValueError) as exc:
            errors[yaml_path.name] = str(exc)

    env_schema_path = config_dir / args.env_schema
    try:
        env_schema = load_json(env_schema_path)
        env_validator = Draft7Validator(env_schema, format_checker=PATH_FORMAT_CHECKER)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        errors[env_schema_path.name] = f"Failed to load environment schema: {exc}"
        env_validator = None

    if env_validator is not None:
        for env_path in iter_env_files(config_dir):
            try:
                values = load_env(env_path)
                env_validator.validate(values)
            except (OSError, ValidationError, ValueError) as exc:
                errors[env_path.name] = str(exc)

    if errors:
        for file_name, message in errors.items():
            print(f"Validation failed for {file_name}: {message}")
        return 1

    print("All configuration files validated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
