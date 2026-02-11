"""Tests for NeonTetraSkin and DiscusSkin renderers."""
import sys
import pytest
import math

pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
from PySide6.QtWidgets import QApplication
pytest.importorskip("PySide6.QtGui", exc_type=ImportError)

from ui.tetra_skin import NeonTetraSkin
from ui.discus_skin import DiscusSkin
from ui.skin import FishSkin


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    return app


def _make_fish_state(x=100, y=100, vx=20, vy=5):
    return {
        "position": [x, y],
        "velocity": [vx, vy],
        "hunger": 10,
        "mood": 80,
        "state": "SCHOOLING",
        "facing_angle": math.atan2(vy, vx),
    }


# --- Neon Tetra Tests ---

def test_tetra_skin_initialization():
    skin = NeonTetraSkin(seed=42)
    assert skin.size_scale == 1.0
    assert skin.opacity == 0.92


def test_tetra_skin_unique_seeds():
    skin1 = NeonTetraSkin(seed=10)
    skin2 = NeonTetraSkin(seed=30)
    assert skin1._hue_offset != skin2._hue_offset


def test_tetra_skin_set_colors():
    skin = NeonTetraSkin(seed=42)
    skin.set_colors([255, 0, 0], [0, 255, 0], [0, 0, 255])


def test_tetra_skin_apply_config():
    skin = NeonTetraSkin(seed=42)

    class FakeConfig:
        def get(self, key):
            return {"size_scale": 1.5}

    skin.apply_config(FakeConfig())
    assert skin.size_scale == 1.5


def test_tetra_phases_initial():
    skin = NeonTetraSkin(seed=42)
    assert skin.time == 0.0
    assert skin.tail_phase == 0.0
    assert skin.breath_phase == 0.0
    assert skin.shimmer_phase == 0.0


def test_tetra_render(qapp):
    from PySide6.QtGui import QPainter, QPixmap
    skin = NeonTetraSkin(seed=42)
    pixmap = QPixmap(200, 200)
    pixmap.fill()
    painter = QPainter(pixmap)
    skin.render(painter, (100, 100), _make_fish_state())
    painter.end()


def test_tetra_render_flipped(qapp):
    from PySide6.QtGui import QPainter, QPixmap
    skin = NeonTetraSkin(seed=42)
    pixmap = QPixmap(200, 200)
    pixmap.fill()
    painter = QPainter(pixmap)
    skin.render(painter, (100, 100), _make_fish_state(vx=-30, vy=5))
    painter.end()


# --- Discus Tests ---

def test_discus_skin_initialization():
    skin = DiscusSkin(seed=42, morph="turquoise")
    assert skin.morph == "turquoise"
    assert skin.size_scale == 1.0
    assert skin.opacity == 0.93


def test_discus_all_morphs():
    for morph in DiscusSkin.MORPHS:
        skin = DiscusSkin(seed=42, morph=morph)
        assert skin.morph == morph
        assert skin.base_col == DiscusSkin.MORPHS[morph]["base"]


def test_discus_morph_count():
    assert len(DiscusSkin.MORPHS) == 5


def test_discus_invalid_morph():
    skin = DiscusSkin(seed=42, morph="nonexistent")
    assert skin.base_col == DiscusSkin.MORPHS["turquoise"]["base"]


def test_discus_skin_set_colors():
    skin = DiscusSkin(seed=42)
    skin.set_colors([100, 200, 150], [50, 100, 75], [200, 250, 220])
    assert skin.base_col == [100, 200, 150]
    assert skin.pattern_col == [50, 100, 75]
    assert skin.bar_col == [200, 250, 220]


def test_discus_lerp():
    skin = DiscusSkin(seed=42)
    assert skin._lerp([0, 0, 0], [100, 200, 50], 0.5) == [50, 100, 25]
    assert skin._lerp([10, 20, 30], [100, 200, 50], 0.0) == [10, 20, 30]
    assert skin._lerp([10, 20, 30], [100, 200, 50], 1.0) == [100, 200, 50]
    assert skin._lerp([0, 0, 0], [100, 200, 50], 2.0) == [100, 200, 50]


def test_discus_apply_config():
    skin = DiscusSkin(seed=42)

    class FakeConfig:
        def get(self, key):
            return {"size_scale": 2.0}

    skin.apply_config(FakeConfig())
    assert skin.size_scale == 2.0


def test_discus_body_flex_initial():
    skin = DiscusSkin(seed=42)
    assert skin.body_flex == 0.0


def test_discus_c_helper(qapp):
    skin = DiscusSkin(seed=42)
    color = skin._c([100, 150, 200], 128)
    assert color.red() == 100
    assert color.green() == 150
    assert color.blue() == 200


def test_discus_render(qapp):
    from PySide6.QtGui import QPainter, QPixmap
    skin = DiscusSkin(seed=42, morph="red_melon")
    pixmap = QPixmap(200, 200)
    pixmap.fill()
    painter = QPainter(pixmap)
    skin.render(painter, (100, 100), _make_fish_state())
    painter.end()


def test_discus_render_all_morphs(qapp):
    from PySide6.QtGui import QPainter, QPixmap
    for morph in DiscusSkin.MORPHS:
        skin = DiscusSkin(seed=42, morph=morph)
        pixmap = QPixmap(200, 200)
        pixmap.fill()
        painter = QPainter(pixmap)
        skin.render(painter, (100, 100), _make_fish_state())
        painter.end()


# --- Betta (Uno) Skin Tests ---

def test_betta_skin_visual_controls_apply_config():
    skin = FishSkin()

    class FakeConfig:
        def get(self, key):
            return {
                "silhouette_strength": 1.35,
                "eye_tracking_strength": 0.4,
                "betta_palette": "mustard_gas",
            }

    skin.apply_config(FakeConfig())
    assert skin.silhouette_strength == pytest.approx(1.35)
    assert skin.eye_tracking_strength == pytest.approx(0.4)


def test_betta_skin_visual_controls_clamped():
    skin = FishSkin()

    class FakeConfig:
        def get(self, key):
            return {
                "silhouette_strength": 9.0,
                "eye_tracking_strength": -3.0,
            }

    skin.apply_config(FakeConfig())
    assert skin.silhouette_strength == pytest.approx(1.9)
    assert skin.eye_tracking_strength == pytest.approx(0.0)


def test_betta_skin_visual_controls_invalid_types_keep_defaults():
    skin = FishSkin()
    default_s = skin.silhouette_strength
    default_e = skin.eye_tracking_strength

    class FakeConfig:
        def get(self, key):
            return {
                "silhouette_strength": "ultra",
                "eye_tracking_strength": object(),
            }

    skin.apply_config(FakeConfig())
    assert skin.silhouette_strength == pytest.approx(default_s)
    assert skin.eye_tracking_strength == pytest.approx(default_e)


def test_betta_independent_palette_set_returns_distinct_pair():
    palettes = FishSkin.independent_palette_set(count=2, preferred="nemo_galaxy")
    assert len(palettes) == 2
    assert palettes[0] != palettes[1]


def test_betta_independent_palette_set_clamps_count():
    palettes = FishSkin.independent_palette_set(count=99, preferred="nemo_galaxy")
    assert len(palettes) == 2
