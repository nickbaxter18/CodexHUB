from src.backend.services import api_service


def test_register_plugin_persists_metadata():
    api_service.registry = api_service.PluginRegistry()  # reset
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
    api_service.register_plugin("payments", "0.2.0")
    api_service.registry.disable("payments")
    assert api_service.list_plugins()["payments"]["enabled"] is False
    api_service.registry.enable("payments")
    assert api_service.list_plugins()["payments"]["enabled"] is True
