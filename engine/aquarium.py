"""
Multi-monitor overlay window system.
Each AquariumSector is a transparent, click-through window on one monitor.
Renders deep sea creatures (jellyfish) with proper coordinate translation.

NOTE: Plants and leaves removed - moved to LUMEX division.
Assistant's division: Deep sea creatures only (jellyfish, etc.)
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QGuiApplication, QPainter, QColor, QRadialGradient, QBrush
import math
from utils.logger import logger


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
    """Transparent overlay window for one monitor, renders deep sea creatures + bubbles."""

    def __init__(self, screen_geometry, sector_id, skin=None, bubble_system=None, config=None):
        super().__init__()
        self.sector_id = sector_id
        self.screen_geometry = screen_geometry
        self.fish_state = None
        self.fish_local_pos = (0, 0)
        self.should_render_fish = False
        self.skin = skin
        self.bubble_system = bubble_system
        self.visible = True
        self.config = config

        # NOTE: Plants and leaves moved to LUMEX division
        # Assistant's division: Deep sea creatures only

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

    def set_visible(self, visible):
        self.visible = visible
        if visible:
            self.show()
        else:
            self.hide()

    def update_fish_state(self, fish_state):
        """Update single creature state (solo mode)."""
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

    def paintEvent(self, event):
        if not self.visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Clear previous frame - CRITICAL for transparent overlays on Windows
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # NOTE: Plants removed - moved to LUMEX division
        # Assistant's division: Deep sea creatures only (jellyfish)

        # Render bubbles
        if self.bubble_system:
            painter.save()
            painter.translate(
                -self.screen_geometry.x(),
                -self.screen_geometry.y()
            )
            self.bubble_system.render(painter)
            painter.restore()

        # Render deep sea creature (jellyfish)
        if self.fish_state and self.should_render_fish and self.skin:
            self.skin.render(painter, self.fish_local_pos, self.fish_state)

        painter.end()
