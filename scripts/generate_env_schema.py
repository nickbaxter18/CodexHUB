"""Generate a JSON Schema representing required CodexHUB environment variables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Type

ROOT = Path(__file__).resolve().parent.parent

if TYPE_CHECKING:  # pragma: no cover - imported only for typing
    from src.common.config_loader import EnvironmentSettings as _EnvironmentSettings


def _load_environment_model() -> "Type[_EnvironmentSettings]":
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.common.config_loader import EnvironmentSettings as _EnvironmentSettings

    return _EnvironmentSettings


DEFAULT_OUTPUT = Path("config/env.schema.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path where the generated schema should be written.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Number of spaces to use when pretty-printing JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    EnvironmentSettings = _load_environment_model()
    schema = EnvironmentSettings.model_json_schema(ref_template="#/$defs/{model}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(schema, handle, indent=args.indent)
        handle.write("\n")

    print(f"Environment schema written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
