import hashlib
import json
from pathlib import Path

from src.backend.services import api_service, health_service


def test_health_snapshot_degraded_without_plugins(tmp_path: Path):
    api_service.registry = api_service.PluginRegistry()
    snapshot = health_service.build_health_snapshot()
    assert snapshot["status"] == "degraded"
    assert snapshot["components"]["plugins"]["count"] == 0


def test_readiness_ready_when_plugins_loaded(tmp_path: Path):
    manifest = {
        "name": "probe-plugin",
        "version": "1.0.0",
        "permissions": [],
        "webhooks": [],
    }
    payload = json.dumps(
        {
            "name": manifest["name"],
            "version": manifest["version"],
            "permissions": manifest["permissions"],
            "webhooks": manifest["webhooks"],
        },
        sort_keys=True,
    )
    manifest["signature"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    plugin_dir = tmp_path / "probe" / "plugin.json"
    plugin_dir.parent.mkdir(parents=True)
    plugin_dir.write_text(json.dumps(manifest), encoding="utf-8")

    api_service.load_plugins_from_directory(tmp_path)
    snapshot = health_service.readiness_probe()
    assert snapshot["ready"] is True
    assert snapshot["status"] == "healthy"
