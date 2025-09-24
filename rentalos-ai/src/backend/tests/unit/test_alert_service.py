from src.backend.services.alert_service import create_alert, list_alerts


def test_alert_creation():
    alert = create_alert("sms", "Test message")
    assert alert.channel == "sms"
    assert list_alerts()
