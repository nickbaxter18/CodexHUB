from fastapi.testclient import TestClient

from src.backend.main import app

client = TestClient(app)


def test_assets_endpoint():
    response = client.get("/api/assets")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_pricing_endpoint():
    response = client.post("/api/pricing/suggestions", json={"asset_id": 1, "duration": 5})
    assert response.status_code == 200
    assert response.json()["asset_id"] == 1


def test_esg_endpoint():
    response = client.post("/api/esg/report", json={"asset_id": 1, "carbon_kg": 100})
    assert response.status_code == 200
    assert "score" in response.json()


def test_plugin_lifecycle_and_health_endpoints():
    reload_response = client.post("/api/plugins/reload", json={})
    assert reload_response.status_code == 202
    data = reload_response.json()
    assert data["plugins"]
    plugin_name = data["plugins"][0]["name"]

    disable_response = client.post(f"/api/plugins/{plugin_name}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False

    enable_response = client.post(f"/api/plugins/{plugin_name}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["enabled"] is True

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] in {"healthy", "degraded"}

    ready_response = client.get("/ready")
    assert ready_response.status_code == 200
    assert ready_response.json()["ready"] is True
