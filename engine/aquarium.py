"""
Multi-monitor overlay window system.
Each AquariumSector is a transparent, click-through window on one monitor.
Renders deep sea creatures (jellyfish) with proper coordinate translation.

NOTE: Plants and leaves removed - moved to LUMEX division.
Assistant's division: Deep sea creatures only (jellyfish, etc.)
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import (
    QGuiApplication,
    QPainter,
    QColor,
    QRadialGradient,
    QBrush,
    QPainterPath,
    QPen,
    QLinearGradient,
)
import math
import random
import time
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

        ambient_cfg = self.config.get("ambient") if self.config and hasattr(self.config, "get") else {}
        if not isinstance(ambient_cfg, dict):
            ambient_cfg = {}

        # Lightweight ambient leaf drift remains part of the base aquarium layer.
        self._leaves_enabled = bool(ambient_cfg.get("falling_leaves_enabled", True))
        self._leaf_cycle_seconds = max(30, int(ambient_cfg.get("falling_leaves_interval_seconds", 5 * 60)))
        self._leaf_burst_min = max(1, int(ambient_cfg.get("falling_leaves_burst_min", 6)))
        self._leaf_burst_max = max(self._leaf_burst_min, int(ambient_cfg.get("falling_leaves_burst_max", 8)))
        self._next_leaf_burst_at = time.time() + random.uniform(30.0, 120.0)
        self._leaf_particles = []
        self._leaf_phase = "idle"  # idle, falling, piled, gust
        self._leaf_phase_started_at = time.time()
        self._last_leaf_update = time.time()

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

    def _spawn_leaf_burst(self):
        """Spawn a small batch of ambient leaves from the top edge."""
        now = time.time()
        self._leaf_particles = []
        leaf_count = random.randint(self._leaf_burst_min, self._leaf_burst_max)
        width = self.screen_geometry.width()
        height = self.screen_geometry.height()

        for _ in range(leaf_count):
            self._leaf_particles.append({
                "x": random.uniform(width * 0.10, width * 0.90),
                "y": random.uniform(-36.0, -8.0),
                "vx": random.uniform(-9.0, 9.0),
                "vy": random.uniform(22.0, 44.0),
                "rot": random.uniform(0.0, 360.0),
                "spin": random.uniform(-46.0, 46.0),
                "size": random.uniform(6.0, 10.0),
                "alpha": random.uniform(150.0, 210.0),
                "grounded": False,
                "ground_y": height - random.uniform(8.0, 24.0),
            })

        self._leaf_phase = "falling"
        self._leaf_phase_started_at = now
        self._last_leaf_update = now

    def _update_leaves(self):
        now = time.time()
        dt = max(0.0, min(0.05, now - self._last_leaf_update))
        self._last_leaf_update = now

        if not self._leaves_enabled:
            self._leaf_particles = []
            self._leaf_phase = "idle"
            return

        if not self._leaf_particles and now >= self._next_leaf_burst_at:
            self._spawn_leaf_burst()

        if not self._leaf_particles:
            return

        all_grounded = True
        if self._leaf_phase == "falling":
            for leaf in self._leaf_particles:
                if leaf["grounded"]:
                    continue
                leaf["vx"] += math.sin(now * 0.8 + leaf["rot"] * 0.01) * 0.28
                leaf["x"] += leaf["vx"] * dt
                leaf["y"] += leaf["vy"] * dt
                leaf["rot"] += leaf["spin"] * dt
                leaf["vy"] = min(78.0, leaf["vy"] + 16.0 * dt)

                if leaf["y"] >= leaf["ground_y"]:
                    leaf["y"] = leaf["ground_y"]
                    leaf["grounded"] = True
                    leaf["vx"] *= 0.2
                    leaf["vy"] = 0.0
                else:
                    all_grounded = False

            if all_grounded:
                self._leaf_phase = "piled"
                self._leaf_phase_started_at = now

        elif self._leaf_phase == "piled":
            for leaf in self._leaf_particles:
                leaf["x"] += math.sin(now * 1.9 + leaf["rot"] * 0.02) * 0.08
                leaf["rot"] += math.sin(now * 0.7 + leaf["x"] * 0.01) * 0.2

            if now - self._leaf_phase_started_at >= 4.0:
                self._leaf_phase = "gust"
                self._leaf_phase_started_at = now

        elif self._leaf_phase == "gust":
            gust = 55.0 + 22.0 * math.sin((now - self._leaf_phase_started_at) * 1.2)
            for leaf in self._leaf_particles:
                leaf["x"] += (gust + random.uniform(-9.0, 9.0)) * dt
                leaf["y"] -= random.uniform(4.0, 12.0) * dt
                leaf["rot"] += leaf["spin"] * 0.6 * dt
                leaf["alpha"] -= 72.0 * dt

            self._leaf_particles = [leaf for leaf in self._leaf_particles if leaf["alpha"] > 4.0]
            if not self._leaf_particles:
                self._leaf_phase = "idle"
                self._next_leaf_burst_at = now + self._leaf_cycle_seconds

    def _draw_leaves(self, painter):
        if not self._leaf_particles:
            return

        painter.save()
        for leaf in self._leaf_particles:
            x = leaf["x"]
            y = leaf["y"]
            if x < -20 or y < -60 or x > self.screen_geometry.width() + 20 or y > self.screen_geometry.height() + 30:
                continue

            alpha = max(0, min(255, int(leaf["alpha"])))
            size = leaf["size"]
            painter.save()
            painter.translate(x, y)
            painter.rotate(leaf["rot"])

            leaf_path = QPainterPath()
            leaf_path.moveTo(0, -size)
            leaf_path.cubicTo(size * 0.9, -size * 0.2, size * 0.75, size * 0.7, 0, size)
            leaf_path.cubicTo(-size * 0.75, size * 0.7, -size * 0.9, -size * 0.2, 0, -size)

            fill = QLinearGradient(0, -size, 0, size)
            fill.setColorAt(0.0, QColor(188, 126, 46, alpha))
            fill.setColorAt(0.55, QColor(153, 94, 34, int(alpha * 0.9)))
            fill.setColorAt(1.0, QColor(108, 62, 20, int(alpha * 0.82)))
            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(QColor(88, 48, 16, int(alpha * 0.78)), 0.8))
            painter.drawPath(leaf_path)

            painter.setPen(QPen(QColor(236, 198, 132, int(alpha * 0.45)), 0.55))
            painter.drawLine(0, int(-size * 0.82), 0, int(size * 0.84))
            painter.restore()

        painter.restore()

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

        if self._leaves_enabled:
            self._update_leaves()
            self._draw_leaves(painter)

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
