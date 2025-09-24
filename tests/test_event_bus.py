"""Unit tests validating the behaviour of the QAEventBus."""

from __future__ import annotations

from typing import Any, List, Tuple

from qa.qa_event_bus import QAEventBus


def test_publish_and_subscribe() -> None:
    """Subscribers should receive payloads published under their event type."""

    bus = QAEventBus()
    received: List[Tuple[str, Any]] = []

    def listener(event_type: str, data: Any) -> None:
        received.append((event_type, data))

    bus.subscribe("example", listener)
    bus.publish("example", {"value": 42})
    assert received == [("example", {"value": 42})]


def test_listener_exception_does_not_block_other_subscribers(capfd) -> None:
    """Errors raised by one subscriber must not prevent other listeners from receiving events."""

    bus = QAEventBus()
    calls: List[str] = []

    def bad_listener(event_type: str, data: Any) -> None:
        raise RuntimeError("listener failure")

    def good_listener(event_type: str, data: Any) -> None:
        calls.append("good")

    bus.subscribe("failing", bad_listener)
    bus.subscribe("failing", good_listener)
    bus.publish("failing", None)

    # Ensure the good listener still executed
    assert calls == ["good"]

    # Ensure the test harness captured the exception without breaking other listeners
    capfd.readouterr()


def test_unsubscribe_removes_listener() -> None:
    """Subscribers removed via ``unsubscribe`` should no longer receive events."""

    bus = QAEventBus()
    calls: List[str] = []

    def listener(event_type: str, data: Any) -> None:
        calls.append("called")

    bus.subscribe("remove_me", listener)
    bus.unsubscribe("remove_me", listener)
    bus.publish("remove_me", None)

    assert calls == []
