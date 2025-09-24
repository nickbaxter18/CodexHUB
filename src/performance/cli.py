"""Command-line helpers for recording CI performance metrics."""

from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path
from typing import Iterable, List, Mapping, MutableSequence, Sequence

from src.performance.metrics_collector import PerformanceCollector

SuiteCommand = Sequence[str]

NODE_QUALITY_COMMANDS: List[SuiteCommand] = [
    ["pnpm", "typecheck"],
    ["pnpm", "lint"],
    ["pnpm", "check-format"],
    ["pnpm", "lint:css"],
    ["pnpm", "test"],
    ["pnpm", "coverage"],
    ["pnpm", "audit", "--audit-level=high"],
]

DOCS_QUALITY_COMMANDS: List[SuiteCommand] = [
    ["pnpm", "lint:md"],
    ["pnpm", "lint:yaml"],
    ["pnpm", "spellcheck"],
    ["pnpm", "lint:editorconfig"],
]

PYTHON_QUALITY_COMMANDS: List[SuiteCommand] = [
    ["python", "scripts/validate_configs.py"],
    ["pytest", "--cov=macro_system", "--cov=meta_agent", "--cov=qa"],
    [
        "bandit",
        "-q",
        "-r",
        "macro_system",
        "meta_agent",
        "qa",
        "-x",
        "macro_system/tests,meta_agent/tests,tests",
    ],
    ["python", "-m", "pip_audit", "-r", "requirements.txt"],
    ["python", "-m", "pip_audit", "-r", "requirements-dev.txt"],
]

QUALITY_SUITES: Mapping[str, List[SuiteCommand]] = {
    "node-quality": NODE_QUALITY_COMMANDS,
    "docs-quality": DOCS_QUALITY_COMMANDS,
    "python-quality": PYTHON_QUALITY_COMMANDS,
}

COMPOSITE_SUITES: Mapping[str, Sequence[str]] = {
    "quality": ["node-quality", "docs-quality", "python-quality"],
}


def _resolve_suite(name: str) -> List[SuiteCommand]:
    if name in QUALITY_SUITES:
        return list(QUALITY_SUITES[name])
    if name in COMPOSITE_SUITES:
        commands: MutableSequence[SuiteCommand] = []
        for child in COMPOSITE_SUITES[name]:
            commands.extend(_resolve_suite(child))
        return list(commands)
    raise KeyError(f"Unknown suite: {name}")


def _run_command(command: SuiteCommand, collector: PerformanceCollector, suite_name: str) -> None:
    start = time.perf_counter()
    metadata = {"command": " ".join(command)}
    try:
        subprocess.run(list(command), check=True)
    except subprocess.CalledProcessError as exc:
        duration = time.perf_counter() - start
        metadata["returncode"] = float(exc.returncode)
        collector.record_metric(
            name=f"{suite_name}::{command[0]}",
            value=duration,
            category="quality",
            metadata=metadata,
        )
        raise
    else:
        duration = time.perf_counter() - start
        collector.record_metric(
            name=f"{suite_name}::{command[0]}",
            value=duration,
            category="quality",
            metadata=metadata,
        )


def run_suite(name: str, *, output_dir: Path | None = None) -> Path:
    collector = PerformanceCollector(output_dir or Path("results/performance"))
    collector.clear_metrics()
    commands = _resolve_suite(name)
    total_start = time.perf_counter()
    for command in commands:
        _run_command(command, collector, name)
    total_duration = time.perf_counter() - total_start
    collector.record_metric(
        name=f"{name}::total",
        value=total_duration,
        category="quality",
        metadata={"command_count": float(len(commands))},
    )
    return collector.save_metrics()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=sorted({*QUALITY_SUITES.keys(), *COMPOSITE_SUITES.keys()}))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for performance snapshots.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    output = run_suite(args.suite, output_dir=args.output_dir)
    print(f"Performance metrics stored at {output}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
