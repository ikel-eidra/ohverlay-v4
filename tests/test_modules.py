import json
import os
import tempfile
import time
from modules.health import HealthModule
from modules.love_notes import LoveNotesModule
from modules.schedule import ScheduleModule


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
        ln.last_check = 0
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


def test_schedule_module_init():
    sm = ScheduleModule()
    assert sm.enabled is True
    assert len(sm.events) > 0


def test_schedule_module_check():
    sm = ScheduleModule()
    msgs = sm.check()
    assert isinstance(msgs, list)
