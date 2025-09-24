#!/usr/bin/env python3
"""Summarise Codex automation health in a single CLI."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

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
        return {
            "compliance": str(exc),
            "compliance_ok": False,
            "report": {},
            "error": str(exc),
        }

    try:
        report: Dict[str, Any] = get_cursor_usage_report()
    except CursorEnforcementError as exc:
        report = {"error": str(exc)}

    compliance_ok = bool(compliance) if isinstance(compliance, bool) else False
    error = report.get("error") if isinstance(report, dict) else None

    return {
        "compliance": compliance,
        "compliance_ok": compliance_ok and error is None,
        "report": report,
        "error": error,
    }


def _render_text_status(
    cursor_report: Dict[str, Any], performance: Optional[Dict[str, Any]], plan_stats: Dict[str, Any]
) -> None:
    print("Codex Automation Status")
    print("=" * 26)

    print("Cursor Compliance:", cursor_report["compliance"])
    if cursor_report.get("error"):
        print(f"  error: {cursor_report['error']}")

    report = cursor_report.get("report", {})
    if isinstance(report, dict):
        usage_stats = cast(Dict[str, Any], report.get("usage_statistics", {}))
        if usage_stats:
            success_rate = usage_stats.get("success_rate", 0)
            try:
                rate_str = f"{float(success_rate):.0%}"
            except (TypeError, ValueError):
                rate_str = str(success_rate)

            print(f"  total usage: {usage_stats.get('total_usage', 0)} | success rate: {rate_str}")
        recommendations = cast(List[str], report.get("recommendations", []))
        if recommendations:
            print("  recommendations:")
            for item in recommendations:
                print(f"    - {item}")
        elif usage_stats:
            print("  recommendations: none")

    if performance:
        print("\nLatest Performance Snapshot:")
        print(f"  file: {performance['file']}")
        print(f"  metrics recorded: {performance['total_metrics']}")
        categories = cast(Dict[str, Dict[str, Any]], performance.get("categories", {}))
        for category, values in categories.items():
            count = values.get("count", 0)
            avg = values.get("avg", 0.0)
            print(f"    - {category}: count={count}, avg={avg:.2f}")
    else:
        print("\nLatest Performance Snapshot: none recorded yet")

    if plan_stats.get("available"):
        print(
            f"\nPlan Artifacts: {plan_stats['plan_files']} plan files, "
            f"{plan_stats['result_files']} result files"
        )
    else:
        print("\nPlan Artifacts: directory not initialised")


def _gather_status() -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Dict[str, Any]]:
    cursor_report = _collect_cursor_report()
    performance_summary = _collect_performance_summary()
    plan_stats = _collect_plan_stats()
    return cursor_report, performance_summary, plan_stats


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarise Codex automation health")
    parser.add_argument("--json", action="store_true", help="Emit status as JSON")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        cursor_report, performance_summary, plan_stats = _gather_status()
    except Exception as exc:  # pragma: no cover - defensive safety net
        logging.exception("Failed to gather automation status")
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            print(f"Error collecting automation status: {exc}", file=sys.stderr)
        return 2

    payload = {
        "cursor": cursor_report,
        "performance": performance_summary,
        "plans": plan_stats,
    }

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        _render_text_status(cursor_report, performance_summary, plan_stats)

    compliance_ok = bool(cursor_report.get("compliance_ok"))
    has_error = cursor_report.get("error") is not None
    return 0 if compliance_ok and not has_error else 1


if __name__ == "__main__":
    sys.exit(main())
