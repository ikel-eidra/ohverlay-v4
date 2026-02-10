"""
Multi-monitor overlay window system.
Each AquariumSector is a transparent, click-through window on one monitor.
Renders fish (single or school) and bubbles with proper coordinate translation.
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QGuiApplication, QPainter
from utils.logger import logger
from ui.skin import FishSkin
from ui.bubbles import BubbleSystem


class MonitorManager:
    """Detects monitors and computes the total canvas bounds."""

    def __init__(self):
        self.screens = QGuiApplication.screens()
        self.geometries = [screen.geometry() for screen in self.screens]
        self.total_bounds = self._calculate_total_bounds()
        logger.info(f"Detected {len(self.screens)} screen(s).")
        for i, rect in enumerate(self.geometries):
            logger.info(f"  Screen {i}: {rect.x()},{rect.y()} {rect.width()}x{rect.height()}")

    def _calculate_total_bounds(self):
        if not self.geometries:
            return QRect(0, 0, 1920, 1080)
        min_x = min(r.x() for r in self.geometries)
        min_y = min(r.y() for r in self.geometries)
        max_x = max(r.x() + r.width() for r in self.geometries)
        max_y = max(r.y() + r.height() for r in self.geometries)
        return QRect(min_x, min_y, max_x - min_x, max_y - min_y)

    def get_total_bounds_tuple(self):
        return (self.total_bounds.x(), self.total_bounds.y(),
                self.total_bounds.width(), self.total_bounds.height())


class AquariumSector(QMainWindow):
    """Transparent overlay window for one monitor, renders fish + bubbles."""

    def __init__(self, screen_geometry, sector_id, skin=None, bubble_system=None):
        super().__init__()
        self.sector_id = sector_id
        self.screen_geometry = screen_geometry
        self.fish_state = None
        self.fish_local_pos = (0, 0)
        self.should_render_fish = False
        self.skin = skin or FishSkin()
        self.bubble_system = bubble_system
        self.visible = True

        # Multi-fish support
        self.school_skins = []      # List of skin objects for school mode
        self.school_states = []     # List of fish states
        self.school_local = []      # List of (local_pos, should_render) tuples
        self.school_mode = False

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowTransparentForInput |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setGeometry(screen_geometry)

        logger.info(f"Aquarium Sector {sector_id} initialized at {screen_geometry}")

    def set_school_skins(self, skins):
        """Set skin renderers for school mode."""
        self.school_skins = skins
        self.school_mode = len(skins) > 0

    def set_visible(self, visible):
        self.visible = visible
        if visible:
            self.show()
        else:
            self.hide()

    def update_fish_state(self, fish_state):
        """Update single fish state (solo mode)."""
        self.fish_state = fish_state
        global_pos = fish_state["position"]
        local_x = global_pos[0] - self.screen_geometry.x()
        local_y = global_pos[1] - self.screen_geometry.y()

        padding = 250
        if (-padding <= local_x <= self.screen_geometry.width() + padding and
                -padding <= local_y <= self.screen_geometry.height() + padding):
            self.fish_local_pos = (local_x, local_y)
            self.should_render_fish = True
        else:
            self.should_render_fish = False

        if self.visible:
            self.update()

    def update_school_states(self, school_states):
        """Update all fish states for school mode."""
        self.school_states = school_states
        self.school_local = []

        padding = 150  # Smaller padding for smaller fish
        for state in school_states:
            global_pos = state["position"]
            local_x = global_pos[0] - self.screen_geometry.x()
            local_y = global_pos[1] - self.screen_geometry.y()

            should_render = (-padding <= local_x <= self.screen_geometry.width() + padding and
                             -padding <= local_y <= self.screen_geometry.height() + padding)
            self.school_local.append(((local_x, local_y), should_render))

        if self.visible:
            self.update()

    def paintEvent(self, event):
        if not self.visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Render bubbles
        if self.bubble_system:
            painter.save()
            painter.translate(
                -self.screen_geometry.x(),
                -self.screen_geometry.y()
            )
            self.bubble_system.render(painter)
            painter.restore()

        # Render fish - school mode or solo mode
        if self.school_mode and self.school_skins and self.school_states:
            for idx, (state, (local_pos, should_render)) in enumerate(
                    zip(self.school_states, self.school_local)):
                if should_render and idx < len(self.school_skins):
                    self.school_skins[idx].render(painter, local_pos, state)
        elif self.fish_state and self.should_render_fish:
            self.skin.render(painter, self.fish_local_pos, self.fish_state)

        painter.end()
