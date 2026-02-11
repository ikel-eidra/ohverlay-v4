import sys
import pytest

pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect
from engine.aquarium import MonitorManager, AquariumSector


def test_monitor_manager():
    app = QApplication.instance() or QApplication(sys.argv)
    mm = MonitorManager()
    bounds = mm.get_total_bounds_tuple()
    assert len(bounds) == 4
    assert bounds[2] > 0
    assert bounds[3] > 0


def test_leaf_burst_spawns_minimum_particles():
    app = QApplication.instance() or QApplication(sys.argv)
    sector = AquariumSector(QRect(0, 0, 800, 600), sector_id=0)
    sector._spawn_leaf_burst()
    assert 6 <= len(sector._leaf_particles) <= 8
    assert sector._leaf_phase == "falling"


def test_leaf_cycle_gust_fades_and_resets_schedule():
    app = QApplication.instance() or QApplication(sys.argv)
    sector = AquariumSector(QRect(0, 0, 800, 600), sector_id=1)
    sector._spawn_leaf_burst()

    # Force gust phase with nearly transparent leaves to complete quickly.
    sector._leaf_phase = "gust"
    sector._leaf_phase_started_at -= 1.0
    sector._last_leaf_update -= 0.05
    for leaf in sector._leaf_particles:
        leaf["alpha"] = 2.0

    sector._update_leaves()
    assert sector._leaf_phase == "idle"
    assert len(sector._leaf_particles) == 0
    assert sector._next_leaf_burst_at > 0


def test_leaf_config_can_disable_effect():
    app = QApplication.instance() or QApplication(sys.argv)

    class FakeConfig:
        def get(self, section, key=None):
            if section == "ambient" and key is None:
                return {
                    "falling_leaves_enabled": False,
                    "falling_leaves_interval_seconds": 300,
                    "falling_leaves_burst_min": 6,
                    "falling_leaves_burst_max": 8,
                }
            return None

    sector = AquariumSector(QRect(0, 0, 800, 600), sector_id=2, config=FakeConfig())
    sector._spawn_leaf_burst()
    sector._update_leaves()
    assert sector._leaf_phase == "idle"
    assert len(sector._leaf_particles) == 0
