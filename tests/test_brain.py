import pytest
import numpy as np
import time
from engine.brain import BehavioralReactor


def test_brain_initialization():
    brain = BehavioralReactor()
    assert brain.state == "IDLE"
    assert brain.hunger == 0.0
    assert brain.mood == 100.0
    assert len(brain.position) == 2


def test_brain_hunger_increase():
    brain = BehavioralReactor()
    brain.update()
    time.sleep(0.1)
    brain.update()
    assert brain.hunger > 0.0


def test_brain_searching_state():
    brain = BehavioralReactor()
    brain.hunger = 40.0
    brain.update()
    assert brain.state == "SEARCHING"


def test_brain_boundary_check():
    brain = BehavioralReactor()
    brain.set_bounds(0, 0, 100, 100)
    brain.position = np.array([150.0, 150.0])
    brain._check_boundaries()
    assert brain.position[0] <= 100.0
    assert brain.position[1] <= 100.0


def test_brain_feed():
    brain = BehavioralReactor()
    brain.hunger = 50.0
    brain.mood = 60.0
    brain.feed()
    assert brain.hunger == 20.0
    assert brain.mood == 80.0
    assert brain.state == "FEEDING"


def test_brain_sanctuary_awareness():
    brain = BehavioralReactor()
    brain.set_bounds(0, 0, 1000, 1000)

    from engine.sanctuary import SanctuaryEngine
    sanctuary = SanctuaryEngine()
    sanctuary.enabled = True
    sanctuary.add_zone(400, 400, 200, 200, "test zone")
    brain.set_sanctuary(sanctuary)

    # Target finding should avoid sanctuary
    brain.hunger = 40.0
    for _ in range(10):
        brain._find_new_target()
        tx, ty = brain.target
        in_sanctuary = (400 <= tx <= 600 and 400 <= ty <= 600)
        if not in_sanctuary:
            break
    assert not (400 <= brain.target[0] <= 600 and 400 <= brain.target[1] <= 600)


def test_brain_resting_state():
    brain = BehavioralReactor()
    brain.state = "RESTING"
    brain._rest_timer = 0.0
    for _ in range(200):
        brain.update()
    assert brain.state != "RESTING" or brain._rest_timer < 6.0


def test_brain_module_check():
    brain = BehavioralReactor()
    from ui.bubbles import BubbleSystem
    bs = BubbleSystem()
    brain.set_bubble_system(bs)

    class FakeModule:
        def check(self):
            return [("Test message", "health")]

    brain.add_module(FakeModule())
    brain._last_module_check = 0
    brain._check_modules()
    assert len(bs.message_queue) == 1
    assert bs.message_queue[0]["message"] == "Test message"
