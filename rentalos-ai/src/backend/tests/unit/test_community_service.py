from src.backend.services.community_service import create_event, join_event, list_events


def test_create_and_join_event():
    event = create_event(1, "Solar Workshop", 30, 10)
    updated = join_event(1, event.id, "Jordan")
    assert updated.attendees == ["Jordan"]
    assert list_events(1)
