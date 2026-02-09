import pytest

pytest.importorskip("PySide6")
from ui.bubbles import Bubble, BubbleSystem


def test_bubble_creation():
    b = Bubble(100, 200)
    assert b.alive
    assert b.message is None
    assert b.opacity == 0.0


def test_bubble_message():
    b = Bubble(100, 200, message="Hello!", category="love")
    assert b.message == "Hello!"
    assert b.category == "love"


def test_bubble_update():
    b = Bubble(100, 200)
    b.update(0.1)
    assert b.y < 200


def test_bubble_system_queue():
    bs = BubbleSystem()
    bs.queue_message("Test message", "health")
    assert len(bs.message_queue) == 1
    assert bs.message_queue[0]["message"] == "Test message"


def test_bubble_system_ambient():
    bs = BubbleSystem()
    bs.last_ambient_time = 0
    bs.update(0.1, 100, 100)
    assert isinstance(bs.bubbles, list)


def test_bubble_system_force_deliver():
    bs = BubbleSystem()
    bs.queue_message("Urgent!", "schedule")
    bs.force_deliver(100, 100)
    assert len(bs.message_queue) == 0
    message_bubbles = [b for b in bs.bubbles if b.message == "Urgent!"]
    assert len(message_bubbles) == 1
