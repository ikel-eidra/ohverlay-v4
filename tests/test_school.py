import pytest
import math
import numpy as np
from engine.school import FishSchool, SchoolFish, SPECIES_PARAMS


def test_school_fish_initialization():
    fish = SchoolFish(0, [500, 400], "neon_tetra")
    assert fish.fish_id == 0
    assert fish.species == "neon_tetra"
    assert len(fish.position) == 2
    assert len(fish.velocity) == 2
    assert fish.state == "SCHOOLING"
    assert fish.mood >= 80


def test_school_fish_state():
    fish = SchoolFish(1, [100, 200], "discus")
    state = fish.get_state()
    assert "position" in state
    assert "velocity" in state
    assert "hunger" in state
    assert "mood" in state
    assert "state" in state
    assert "facing_angle" in state
    assert state["position"] == [100.0, 200.0]


def test_species_params_exist():
    assert "neon_tetra" in SPECIES_PARAMS
    assert "discus" in SPECIES_PARAMS
    assert "betta" in SPECIES_PARAMS


def test_species_params_fields():
    for species, params in SPECIES_PARAMS.items():
        assert "max_speed" in params
        assert "cruise_speed" in params
        assert "separation_radius" in params
        assert "alignment_radius" in params
        assert "cohesion_radius" in params
        assert "turn_speed" in params


def test_school_creation():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=6)
    assert len(school.fish) == 6
    assert school.species == "neon_tetra"


def test_school_creation_discus():
    school = FishSchool((0, 0, 1920, 1080), species="discus", count=5)
    assert len(school.fish) == 5
    assert school.species == "discus"


def test_school_count_clamped():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=6)
    school.set_count(20)  # Should clamp to 12
    assert len(school.fish) == 12

    school.set_count(0)  # Should clamp to 1
    assert len(school.fish) == 1


def test_school_set_count_add():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=4)
    assert len(school.fish) == 4
    school.set_count(8)
    assert len(school.fish) == 8


def test_school_set_count_remove():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=10)
    school.set_count(3)
    assert len(school.fish) == 3


def test_school_update():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=6)
    # Record initial positions
    initial_positions = [f.position.copy() for f in school.fish]
    # Force a meaningful dt so fish actually move
    school.last_update -= 0.05
    school.update()
    # At least some fish should have moved
    moved = False
    for i, fish in enumerate(school.fish):
        if not np.allclose(fish.position, initial_positions[i]):
            moved = True
            break
    assert moved


def test_school_get_all_states():
    school = FishSchool((0, 0, 1920, 1080), species="discus", count=3)
    states = school.get_all_states()
    assert len(states) == 3
    for state in states:
        assert "position" in state
        assert "velocity" in state
        assert "facing_angle" in state


def test_school_fish_stay_in_bounds():
    school = FishSchool((0, 0, 800, 600), species="neon_tetra", count=6)
    for _ in range(100):
        school.update()
    for fish in school.fish:
        assert fish.position[0] >= 30
        assert fish.position[0] <= 770
        assert fish.position[1] >= 30
        assert fish.position[1] <= 570


def test_school_facing_no_somersault():
    """Verify that facing angle changes smoothly (no 360-degree spins)."""
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=4)
    for _ in range(50):
        prev_angles = [f.facing_angle for f in school.fish]
        school.update()
        for i, fish in enumerate(school.fish):
            diff = abs(fish.facing_angle - prev_angles[i])
            # Normalize to [0, pi]
            if diff > math.pi:
                diff = 2 * math.pi - diff
            # Should never jump more than ~1 radian per frame
            assert diff < 1.5, f"Fish {i} jumped {diff} radians in one frame!"


def test_school_sanctuary_awareness():
    from engine.sanctuary import SanctuaryEngine
    sanctuary = SanctuaryEngine()
    sanctuary.enabled = True
    sanctuary.add_zone(400, 300, 200, 200, "test zone")

    school = FishSchool((0, 0, 1000, 800), species="neon_tetra", count=6)
    school.set_sanctuary(sanctuary)

    # Run many updates - fish should tend to avoid sanctuary zone
    for _ in range(200):
        school.update()

    # Just verify it doesn't crash - sanctuary avoidance is a soft force
    states = school.get_all_states()
    assert len(states) == 6


def test_neon_tetra_school_not_pathologically_clumped():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=10)
    for _ in range(120):
        school.last_update -= 0.033
        school.update()

    positions = np.array([f.position for f in school.fish])
    center = positions.mean(axis=0)
    dists = np.linalg.norm(positions - center, axis=1)
    # Expect school spread ring, not all fish collapsed into a tiny center cluster.
    assert float(dists.mean()) > 30.0


def test_school_speed_scale_clamped():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=4)
    school.set_speed_scale(-99)
    assert school._speed_scale == pytest.approx(0.35)
    school.set_speed_scale(99)
    assert school._speed_scale == pytest.approx(2.0)


def test_school_speed_scale_caps_velocity():
    school = FishSchool((0, 0, 1920, 1080), species="neon_tetra", count=1)
    school.set_speed_scale(0.5)

    fish = school.fish[0]
    fish.velocity = np.array([900.0, 0.0], dtype=float)

    school.last_update -= 0.05
    school.update()

    max_allowed = SPECIES_PARAMS["neon_tetra"]["max_speed"] * school._speed_scale * fish._speed_mult
    assert float(np.linalg.norm(fish.velocity)) <= max_allowed + 1e-6
