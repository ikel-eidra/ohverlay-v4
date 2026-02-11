"""
Multi-monitor overlay window system.
Each AquariumSector is a transparent, click-through window on one monitor.
Renders fish (single or school) and bubbles with proper coordinate translation.
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QGuiApplication, QPainter, QColor, QRadialGradient, QBrush, QPainterPath, QPen, QLinearGradient
import time
import math
import random
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

        # Procedural plant bed (8h growth to top, then trim back to 3/5 height).
        self._plant_cycle_start = time.time()
        self._plant_grow_seconds = 8 * 60 * 60
        self._plant_trim_ratio = 0.60
        self._plant_stems = self._build_plant_layout()

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

        for state in school_states:
            species = state.get("species", "neon_tetra")
            padding = 320 if species == "discus" else 220
            global_pos = state["position"]
            local_x = global_pos[0] - self.screen_geometry.x()
            local_y = global_pos[1] - self.screen_geometry.y()

            should_render = (-padding <= local_x <= self.screen_geometry.width() + padding and
                             -padding <= local_y <= self.screen_geometry.height() + padding)
            self.school_local.append(((local_x, local_y), should_render))

        if self.visible:
            self.update()


    def _build_plant_layout(self):
        stems = []
        width = max(200, self.screen_geometry.width())
        count = max(7, min(18, width // 150))
        for _ in range(int(count)):
            stems.append({
                "x": random.uniform(20, max(21, self.screen_geometry.width() - 20)),
                "phase": random.uniform(0.0, math.pi * 2),
                "sway": random.uniform(7.0, 16.0),
                "thickness": random.uniform(2.2, 4.2),
                "h_mult": random.uniform(0.82, 1.08),
            })
        return stems

    def _plant_height_ratio(self):
        elapsed = max(0.0, time.time() - self._plant_cycle_start)
        if elapsed >= self._plant_grow_seconds:
            self._plant_cycle_start = time.time()
            elapsed = 0.0
        grow_t = min(1.0, elapsed / self._plant_grow_seconds)
        return self._plant_trim_ratio + (1.0 - self._plant_trim_ratio) * grow_t

    def _draw_plants(self, painter):
        if not self._plant_stems:
            return
        h = self.screen_geometry.height()
        waterline = 8
        bottom = h + 5
        growth_ratio = self._plant_height_ratio()
        t = time.time()

        for stem in self._plant_stems:
            stem_h = h * 0.92 * growth_ratio * stem["h_mult"]
            top_y = max(waterline, bottom - stem_h)
            x = stem["x"]
            sway = math.sin(t * 0.42 + stem["phase"]) * stem["sway"]

            path = QPainterPath()
            path.moveTo(x, bottom)
            path.cubicTo(
                x + sway * 0.3, bottom - stem_h * 0.32,
                x - sway * 0.8, bottom - stem_h * 0.66,
                x + sway, top_y
            )

            grad = QLinearGradient(x, bottom, x, top_y)
            grad.setColorAt(0.0, QColor(30, 110, 72, 190))
            grad.setColorAt(0.55, QColor(72, 190, 112, 170))
            grad.setColorAt(1.0, QColor(168, 244, 188, 130))
            pen = QPen(QBrush(grad), stem["thickness"])
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawPath(path)

            # Add a few soft leaf highlights so plants are visible on bright desktops.
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(150, 235, 170, 92))
            for i in range(1, 4):
                ly = bottom - stem_h * (0.25 + i * 0.18)
                lx = x + math.sin(stem["phase"] + i * 1.2 + t * 0.5) * (4.5 + i * 1.8)
                painter.drawEllipse(int(lx - 2), int(ly - 2), 5, 5)

    def _draw_pellets(self, painter, pellets):
        if not pellets:
            return
        for gx, gy in pellets:
            lx = gx - self.screen_geometry.x()
            ly = gy - self.screen_geometry.y()
            if lx < -20 or ly < -20 or lx > self.screen_geometry.width() + 20 or ly > self.screen_geometry.height() + 20:
                continue
            grad = QRadialGradient(lx, ly, 5.5)
            grad.setColorAt(0.0, QColor(245, 214, 130, 220))
            grad.setColorAt(0.65, QColor(195, 145, 72, 210))
            grad.setColorAt(1.0, QColor(110, 74, 36, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(int(lx - 4), int(ly - 4), 8, 8)

    def paintEvent(self, event):
        if not self.visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Clear previous frame - CRITICAL for transparent overlays on Windows
        # Without this, old pixels persist and fish leave trails
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Render plant bed (ambient background realism)
        self._draw_plants(painter)

        # Render bubbles
        if self.bubble_system:
            painter.save()
            painter.translate(
                -self.screen_geometry.x(),
                -self.screen_geometry.y()
            )
            self.bubble_system.render(painter)
            painter.restore()

        # Render symbolic feed pellets (solo mode)
        if self.fish_state:
            self._draw_pellets(painter, self.fish_state.get("pellets", []))

        # Render fish - school mode or solo mode
        if self.school_mode and self.school_skins and self.school_states:
            for idx, (state, (local_pos, should_render)) in enumerate(
                    zip(self.school_states, self.school_local)):
                if should_render and idx < len(self.school_skins):
                    self.school_skins[idx].render(painter, local_pos, state)
        elif self.fish_state and self.should_render_fish:
            self.skin.render(painter, self.fish_local_pos, self.fish_state)

        painter.end()
