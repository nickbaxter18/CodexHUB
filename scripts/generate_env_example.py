"""Generate the canonical `.env.example` file from a structured definition.

The repository previously maintained environment variables manually which led to
configuration drift across documentation and automation scripts. This utility
keeps the example file in sync by treating the environment specification as a
single source of truth. Run the script directly (or via `pnpm run env:example`)
whenever variables change, and invoke it with `--check` in CI to ensure the file
was regenerated.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class EnvVar:
    """Represents a single environment variable entry."""

    name: str
    default: str
    comment: str | None = None


@dataclass(frozen=True)
class EnvSection:
    """Logical grouping of related environment variables."""

    title: str
    variables: Sequence[EnvVar]
    footer_comment: str | None = None


ENV_SECTIONS: Sequence[EnvSection] = (
    EnvSection(
        "Core runtime",
        (
            EnvVar("PORT", "4000"),
            EnvVar("NODE_ENV", "development"),
            EnvVar("SESSION_SECRET", "replace-with-strong-secret"),
        ),
    ),
    EnvSection(
        "Credentials",
        (
            EnvVar("OPENAI_API_KEY", "changeme"),
            EnvVar("CURSOR_API_KEY", ""),
            EnvVar("CURSOR_API_URL", "https://api.cursor.sh"),
        ),
    ),
    EnvSection(
        "Machine learning experiment tracking",
        (
            EnvVar("MLFLOW_TRACKING_URI", "./results/mlruns"),
            EnvVar("MLFLOW_REGISTRY_URI", "./results/mlruns"),
            EnvVar("MLFLOW_EXPERIMENT_NAME", "CodexHUB-Baseline"),
        ),
    ),
    EnvSection(
        "Configuration locations",
        (
            EnvVar("PIPELINE_CONFIG_PATH", "config/default.yaml"),
            EnvVar("GOVERNANCE_CONFIG_PATH", "config/governance.yaml"),
            EnvVar("METRICS_CONFIG_PATH", "config/metrics.yaml"),
        ),
    ),
    EnvSection(
        "Observability outputs",
        (
            EnvVar("PERFORMANCE_RESULTS_DIR", "results/performance"),
            EnvVar("AUDIT_LOG_DIR", "results/audit"),
            EnvVar("MODEL_CARD_DIR", "docs/model_cards"),
        ),
    ),
    EnvSection(
        'Automation toggles (set to "true" to enable locally)',
        (
            EnvVar("CURSOR_AUTO_INVOCATION_ENABLED", "false"),
            EnvVar("CURSOR_MONITOR_INTERVAL", "5"),
            EnvVar("CURSOR_FILE_PATTERNS", '"**/*.tsx,**/*.py,**/*.md,**/*.js,**/*.ts"'),
        ),
    ),
    EnvSection(
        "Knowledge ingestion",
        (
            EnvVar("KNOWLEDGE_AUTO_LOAD", "false"),
            EnvVar(
                "KNOWLEDGE_NDJSON_PATHS",
                '"Brain docs cleansed .ndjson,Bundle cleansed .ndjson"',
            ),
            EnvVar(
                "KNOWLEDGE_WATCH_INTERVAL",
                "",
                comment="Leave blank (or set to a positive number) to enable filesystem watching.",
            ),
        ),
    ),
    EnvSection(
        "Mobile controls",
        (
            EnvVar("MOBILE_CONTROL_ENABLED", "false"),
            EnvVar("MOBILE_NOTIFICATIONS_ENABLED", "false"),
            EnvVar("MOBILE_APP_PORT", "3001"),
        ),
    ),
    EnvSection(
        "Brain blocks integration",
        (
            EnvVar("BRAIN_BLOCKS_AUTO_LOAD", "false"),
            EnvVar("BRAIN_BLOCKS_DATA_SOURCE", '"Brain docs cleansed .ndjson"'),
            EnvVar("BRAIN_BLOCKS_QUERY_DEPTH", "summary"),
        ),
    ),
    EnvSection(
        "Performance monitoring",
        (
            EnvVar("CURSOR_PERFORMANCE_MONITORING", "false"),
            EnvVar("CURSOR_USAGE_TRACKING", "false"),
            EnvVar("CURSOR_COMPLIANCE_REPORTING", "false"),
        ),
    ),
)


def _render_section(section: EnvSection) -> list[str]:
    lines: list[str] = [f"# {section.title}"]
    for variable in section.variables:
        if variable.comment:
            for comment_line in variable.comment.splitlines():
                lines.append(f"# {comment_line}".rstrip())
        lines.append(f"{variable.name}={variable.default}")
    if section.footer_comment:
        for comment_line in section.footer_comment.splitlines():
            lines.append(f"# {comment_line}".rstrip())
    lines.append("")
    return lines


def render_env_file(sections: Iterable[EnvSection]) -> str:
    lines: list[str] = []
    for section in sections:
        lines.extend(_render_section(section))
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if .env.example is not up to date",
    )
    args = parser.parse_args(argv)

    rendered = render_env_file(ENV_SECTIONS)
    target = Path(".env.example")
    if args.check:
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        if existing != rendered:
            print(".env.example is out of date. Run `python scripts/generate_env_example.py`.")
            return 1
        return 0

    target.write_text(rendered, encoding="utf-8")
    print("Wrote .env.example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
