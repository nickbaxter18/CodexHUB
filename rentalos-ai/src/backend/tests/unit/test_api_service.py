import hashlib
import json
from pathlib import Path

from src.backend.plugins.runtime import EnergyTradeContext, PricingContext
from src.backend.services import api_service


def test_register_plugin_persists_metadata():
    api_service.registry = api_service.PluginRegistry()  # reset
    api_service._auto_load_attempted = False
    plugin = api_service.register_plugin(
        "green-energy",
        "1.0.0",
        description="Aggregates renewable energy providers",
        permissions=["energy:read"],
        webhooks=["https://example.com/hook"],
        enabled=False,
    )
    assert plugin.enabled is False
    summary = api_service.list_plugins()
    assert "green-energy" in summary
    assert summary["green-energy"]["permissions"] == ["energy:read"]


def test_registry_enable_disable_cycle():
    api_service.registry = api_service.PluginRegistry()  # reset
    api_service._auto_load_attempted = False
    api_service.register_plugin("payments", "0.2.0")
    api_service.registry.disable("payments")
    assert api_service.list_plugins()["payments"]["enabled"] is False
    api_service.registry.enable("payments")
    assert api_service.list_plugins()["payments"]["enabled"] is True


def _signature(manifest: dict) -> str:
    payload = json.dumps(
        {
            "name": manifest["name"],
            "version": manifest["version"],
            "permissions": manifest.get("permissions", []),
            "webhooks": manifest.get("webhooks", []),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_load_plugins_from_directory(tmp_path: Path):
    manifest = {
        "name": "test-plugin",
        "version": "0.1.0",
        "permissions": ["example:read"],
        "webhooks": [],
        "description": "Test plugin",
    }
    manifest["signature"] = _signature(manifest)
    plugin_dir = tmp_path / "sample" / "plugin.json"
    plugin_dir.parent.mkdir(parents=True)
    plugin_dir.write_text(json.dumps(manifest), encoding="utf-8")

    loaded, errors = api_service.load_plugins_from_directory(tmp_path)
    assert not errors
    assert len(loaded) == 1
    assert api_service.list_plugins()["test-plugin"]["version"] == "0.1.0"


def test_load_plugins_reports_signature_error(tmp_path: Path):
    manifest = {
        "name": "bad-plugin",
        "version": "0.0.1",
        "permissions": [],
        "webhooks": [],
        "signature": "not-valid",
    }
    plugin_dir = tmp_path / "sample" / "plugin.json"
    plugin_dir.parent.mkdir(parents=True)
    plugin_dir.write_text(json.dumps(manifest), encoding="utf-8")

    loaded, errors = api_service.load_plugins_from_directory(tmp_path)
    assert loaded == []
    assert errors and "Signature mismatch" in errors[0]


def test_enable_disable_helpers_return_payload(tmp_path: Path):
    manifest = {
        "name": "toggle-plugin",
        "version": "2.0.0",
        "permissions": [],
        "webhooks": [],
    }
    manifest["signature"] = _signature(manifest)
    plugin_dir = tmp_path / "toggle" / "plugin.json"
    plugin_dir.parent.mkdir(parents=True)
    plugin_dir.write_text(json.dumps(manifest), encoding="utf-8")

    api_service.load_plugins_from_directory(tmp_path)
    assert api_service.get_plugin("toggle-plugin")["enabled"] is True
    payload = api_service.disable_plugin("toggle-plugin")
    assert payload["enabled"] is False
    payload = api_service.enable_plugin("toggle-plugin")
    assert payload["enabled"] is True


def test_collect_pricing_adjustments_from_default_plugins():
    api_service.registry = api_service.PluginRegistry()
    api_service._auto_load_attempted = False
    loaded, errors = api_service.reload_default_plugins()
    assert loaded
    assert not errors
    context = PricingContext(
        asset_id=9,
        base_price=180.0,
        occupancy=0.97,
        esg_score=88.0,
        duration=21,
    )
    adjustments = api_service.collect_pricing_adjustments(context)
    assert any(name == "equitable-pricing" for name, _ in adjustments)


def test_collect_energy_recommendations_from_default_plugins():
    api_service.registry = api_service.PluginRegistry()
    api_service._auto_load_attempted = False
    loaded, errors = api_service.reload_default_plugins()
    assert loaded
    assert not errors
    context = EnergyTradeContext(
        asset_id=3,
        kilowatt_hours=20.0,
        direction="buy",
        market_price=0.19,
    )
    recommendations = api_service.collect_energy_recommendations(context)
    assert any(name == "energy-optimizer" for name, _ in recommendations)
