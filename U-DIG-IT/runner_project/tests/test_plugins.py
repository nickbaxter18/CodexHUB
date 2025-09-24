from pathlib import Path

from fastapi.testclient import TestClient

from src.api.server import ORCHESTRATOR, app
from src.utils.plugin_loader import PluginLoader


def create_plugin(directory: Path) -> None:
    module = directory / "demo_plugin.py"
    module.write_text(
        "from src.plugins import PluginRegistry\n\n"
        "def register(registry: PluginRegistry):\n"
        "    registry.register_command('demo', lambda: 'ok')\n"
        "    return {'name': 'demo', 'description': 'Demo plugin', 'version': '1.0.0'}\n"
    )


def test_plugin_loader_and_endpoints(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    create_plugin(plugin_dir)

    loader = PluginLoader(plugin_directory=plugin_dir)
    loaded = loader.load_plugins()
    assert loaded and loaded[0].name == "demo"

    metadata = loader.set_enabled("demo", False)
    assert not metadata.enabled

    original_loader = ORCHESTRATOR.plugin_loader
    ORCHESTRATOR.plugin_loader = loader

    try:
        with TestClient(app) as client:
            listing = client.get("/plugins")
            assert listing.status_code == 200
            body = listing.json()
            assert body["plugins"][0]["name"] == "demo"

            reload_response = client.post("/plugins/reload")
            assert reload_response.status_code == 200
            toggle_response = client.post("/plugins/toggle", json={"name": "demo", "enabled": True})
            assert toggle_response.status_code == 200
            toggled = toggle_response.json()
            assert toggled["status"] == "enabled"
    finally:
        ORCHESTRATOR.plugin_loader = original_loader
