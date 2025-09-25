from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.performance import cli


def test_run_suite_records_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(command: list[str], check: bool) -> None:  # noqa: FBT001
        calls.append(command)

    monkeypatch.setattr(cli.subprocess, "run", _fake_run)
    output_path = cli.run_suite(
        "python-quality",
        output_dir=tmp_path,
        skip=["pip_audit"],
        max_workers=2,
    )
    assert output_path.parent == tmp_path
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total_metrics"] >= 1
    assert calls, "expected commands to be executed"
    assert all("pip_audit" not in " ".join(cmd) for cmd in calls)
    total_metric = next(
        metric for metric in payload["metrics"] if metric["name"].endswith("::total")
    )
    assert total_metric["metadata"]["skipped"] >= 1
    assert total_metric["metadata"]["max_workers"] == 2.0


def test_main_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.subprocess, "run", lambda command, check: None)
    exit_code = cli.main(
        [
            "docs-quality",
            "--output-dir",
            str(tmp_path),
            "--skip",
            "spellcheck",
            "--max-workers",
            "3",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Performance metrics stored" in captured.out
    files = list(tmp_path.glob("performance_metrics_*.json"))
    assert files
