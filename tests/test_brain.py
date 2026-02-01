import pytest
import numpy as np
from engine.brain import BehavioralReactor

def test_brain_initialization():
    brain = BehavioralReactor()
    assert brain.state == "IDLE"
    assert brain.hunger == 0.0
    assert len(brain.position) == 2

def test_brain_hunger_increase():
    brain = BehavioralReactor()
    brain.update() # First update to set last_update
    import time
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
    assert brain.position[0] == 100.0
    assert brain.position[1] == 100.0
