import json
import os
import tempfile
import time
from modules.health import HealthModule
from modules.love_notes import LoveNotesModule
from modules.schedule import ScheduleModule
from modules.telegram_bridge import TelegramBridge
from modules.webhook_server import WebhookServer


def test_health_module_init():
    hm = HealthModule()
    assert hm.enabled is True
    assert "water" in hm.intervals


def test_health_module_check_no_trigger():
    hm = HealthModule()
    msgs = hm.check()
    assert len(msgs) == 0


def test_health_module_check_trigger():
    hm = HealthModule()
    hm.last_triggered["water"] = time.time() - 9999
    msgs = hm.check()
    water_msgs = [m for m in msgs if m[1] == "health"]
    assert len(water_msgs) >= 1


def test_health_module_with_no_llm():
    """Health module should work fine without LLM (fallback to static)."""
    hm = HealthModule(llm_brain=None)
    hm.last_triggered["water"] = time.time() - 9999
    msgs = hm.check()
    assert len(msgs) >= 1
    assert msgs[0][1] == "health"


def test_love_notes_no_path():
    ln = LoveNotesModule()
    msgs = ln.check()
    assert len(msgs) == 0


def test_love_notes_read_file():
    ln = LoveNotesModule()
    ln.check_interval = 0

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"message": "I believe in you"}, f)
        path = f.name

    try:
        ln.set_source_path(path)
        msgs = ln.check()
        assert len(msgs) == 1
        assert msgs[0][0] == "I believe in you"
        assert msgs[0][1] == "love"

        # Second check should not re-deliver
        ln.last_file_check = 0
        msgs2 = ln.check()
        assert len(msgs2) == 0
    finally:
        os.unlink(path)


def test_love_notes_array_format():
    ln = LoveNotesModule()
    ln.check_interval = 0

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"notes": [
            {"message": "Note 1"},
            {"message": "Note 2"},
        ]}, f)
        path = f.name

    try:
        ln.set_source_path(path)
        msgs = ln.check()
        assert len(msgs) == 2
    finally:
        os.unlink(path)


def test_love_notes_multi_source():
    """Love notes should aggregate from file + telegram + webhook."""
    ln = LoveNotesModule()
    ln.check_interval = 0

    # Mock telegram bridge
    class FakeTelegram:
        def check(self):
            return [("Telegram love!", "love")]

    # Mock webhook
    class FakeWebhook:
        def check(self):
            return [("WhatsApp love!", "love")]

    ln.set_telegram_bridge(FakeTelegram())
    ln.set_webhook_server(FakeWebhook())

    msgs = ln.check()
    # Should have telegram + webhook messages (no file since no path set)
    assert len(msgs) == 2
    texts = [m[0] for m in msgs]
    assert "Telegram love!" in texts
    assert "WhatsApp love!" in texts


def test_telegram_bridge_init():
    tb = TelegramBridge()
    assert tb.enabled is False
    assert tb.token == ""


def test_telegram_bridge_check_empty():
    tb = TelegramBridge()
    msgs = tb.check()
    assert len(msgs) == 0


def test_webhook_server_init():
    ws = WebhookServer()
    assert ws.enabled is False
    assert ws.port == 7277


def test_webhook_server_check_empty():
    ws = WebhookServer()
    msgs = ws.check()
    assert len(msgs) == 0


def test_webhook_server_message_queue():
    ws = WebhookServer()
    ws.enabled = True
    ws._messages.append({"text": "Hello from WhatsApp", "sender": "Mahal", "source": "whatsapp"})
    msgs = ws.check()
    assert len(msgs) == 1
    assert msgs[0][1] == "love"
    assert "Hello from WhatsApp" in msgs[0][0]


def test_schedule_module_init():
    sm = ScheduleModule()
    assert sm.enabled is True
    assert len(sm.events) > 0


def test_schedule_module_check():
    sm = ScheduleModule()
    msgs = sm.check()
    assert isinstance(msgs, list)
