#!/usr/bin/env python3
"""Validate governance configuration files against their JSON Schemas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from jsonschema import ValidationError, validate

CONFIG_SCHEMA_MAP: Dict[str, str] = {
    "governance.json": "governance.schema.json",
    "agents.json": "agents.schema.json",
    "qa_policies.json": "qa_policies.schema.json",
    "qa_rules.json": "qa_rules.schema.json",
    "drift.json": "drift.schema.json",
}


def validate_file(config_dir: Path, file_name: str, schema_name: str) -> None:
    """Validate a configuration file against its schema."""

    config_path = config_dir / file_name
    schema_path = config_dir / schema_name
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validate(payload, schema)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-dir", default="config", help="Directory containing configuration files"
    )
    args = parser.parse_args()
    config_dir = Path(args.config_dir)
    errors: Dict[str, str] = {}
    for file_name, schema_name in CONFIG_SCHEMA_MAP.items():
        try:
            validate_file(config_dir, file_name, schema_name)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:  # type: ignore[arg-type]
            errors[file_name] = str(exc)
    if errors:
        for file_name, message in errors.items():
            print(f"Validation failed for {file_name}: {message}")
        return 1
    print("All configuration files validated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
