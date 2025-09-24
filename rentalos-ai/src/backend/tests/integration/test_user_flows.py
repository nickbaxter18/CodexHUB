from fastapi.testclient import TestClient

from src.backend.main import app

client = TestClient(app)


def test_tenant_flow():
    pricing = client.post("/api/pricing/suggestions", json={"asset_id": 1, "duration": 7}).json()
    plan = client.post(
        "/api/payments/plan",
        json={"lease_id": 1, "monthly_amount": 2000, "participants": ["A", "B"]},
    ).json()
    event = client.post("/api/community/events", json={"asset_id": 1, "title": "Meetup"}).json()
    assert pricing["asset_id"] == 1
    assert plan["lease_id"] == 1
    assert event["asset_id"] == 1
