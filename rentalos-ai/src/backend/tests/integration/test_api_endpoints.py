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
