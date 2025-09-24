#!/usr/bin/env python3
"""Summarise Codex automation health in a single CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, Union, cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ENFORCEMENT_SPEC = importlib.util.spec_from_file_location(
    "codex_cursor_enforcement", PROJECT_ROOT / "src" / "cursor" / "enforcement.py"
)
if ENFORCEMENT_SPEC is None or ENFORCEMENT_SPEC.loader is None:
    raise RuntimeError("Unable to load cursor enforcement module")

_enforcement = importlib.util.module_from_spec(ENFORCEMENT_SPEC)
ENFORCEMENT_SPEC.loader.exec_module(_enforcement)

CursorEnforcementError = cast(Type[Exception], getattr(_enforcement, "CursorEnforcementError"))
validate_cursor_compliance = cast(
    Callable[[], bool], getattr(_enforcement, "validate_cursor_compliance")
)
get_cursor_usage_report = cast(
    Callable[[], Dict[str, Any]], getattr(_enforcement, "get_cursor_usage_report")
)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return cast(Dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return None


def _collect_performance_summary() -> Optional[Dict[str, Any]]:
    results_dir = PROJECT_ROOT / "results" / "performance"
    if not results_dir.exists():
        return None

    snapshots = sorted(results_dir.glob("performance_metrics_*.json"))
    if not snapshots:
        return None

    latest = snapshots[-1]
    data = _load_json(latest)
    if not data:
        return None

    summary = data.get("summary", {})
    return {
        "file": str(latest.relative_to(PROJECT_ROOT)),
        "total_metrics": summary.get("total_metrics", 0),
        "categories": summary.get("categories", {}),
        "timestamp": summary.get("timestamp"),
    }


def _collect_plan_stats() -> Dict[str, Any]:
    plans_dir = PROJECT_ROOT / "plans"
    if not plans_dir.exists():
        return {"available": False}

    plan_files = list(plans_dir.glob("**/*.json"))
    result_files = list((PROJECT_ROOT / "results").glob("**/*.json"))
    return {
        "available": True,
        "plan_files": len(plan_files),
        "result_files": len(result_files),
    }


def _collect_cursor_report() -> Dict[str, Any]:
    try:
        compliance: Union[bool, str] = validate_cursor_compliance()
    except CursorEnforcementError as exc:
        compliance = str(exc)

    try:
        report: Dict[str, Any] = get_cursor_usage_report()
    except CursorEnforcementError as exc:
        report = {"error": str(exc)}

    return {"compliance": compliance, "report": report}


def display_status() -> None:
    print("Codex Automation Status")
    print("=" * 26)

    cursor_report = _collect_cursor_report()
    print("Cursor Compliance:", cursor_report["compliance"])
    if "report" in cursor_report:
        usage_stats = cursor_report["report"].get("usage_statistics", {})
        if usage_stats:
            success_rate = usage_stats.get("success_rate", 0)
            try:
                rate_str = f"{float(success_rate):.0%}"
            except (TypeError, ValueError):
                rate_str = str(success_rate)

            print(
                f"  total usage: {usage_stats.get('total_usage', 0)} | " f"success rate: {rate_str}"
            )
        recommendations = cursor_report["report"].get("recommendations", [])
        if recommendations:
            print("  recommendations:")
            for item in recommendations:
                print(f"    - {item}")
        elif usage_stats:
            print("  recommendations: none")

    performance_summary = _collect_performance_summary()
    if performance_summary:
        print("\nLatest Performance Snapshot:")
        print(f"  file: {performance_summary['file']}")
        print(f"  metrics recorded: {performance_summary['total_metrics']}")
        if performance_summary["categories"]:
            for category, values in performance_summary["categories"].items():
                print(
                    f"    - {category}: count={values.get('count', 0)}, "
                    f"avg={values.get('avg', 0):.2f}"
                )
    else:
        print("\nLatest Performance Snapshot: none recorded yet")

    plan_stats = _collect_plan_stats()
    if plan_stats.get("available"):
        print(
            f"\nPlan Artifacts: {plan_stats['plan_files']} plan files, "
            f"{plan_stats['result_files']} result files"
        )
    else:
        print("\nPlan Artifacts: directory not initialised")


if __name__ == "__main__":
    display_status()
