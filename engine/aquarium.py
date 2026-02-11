"""
Multi-monitor overlay window system.
Each AquariumSector is a transparent, click-through window on one monitor.
Renders fish (single or school) and bubbles with proper coordinate translation.
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, QRect, QPointF
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

    def __init__(self, screen_geometry, sector_id, skin=None, bubble_system=None, config=None):
        super().__init__()
        self.sector_id = sector_id
        self.screen_geometry = screen_geometry
        self.fish_state = None
        self.fish_local_pos = (0, 0)
        self.should_render_fish = False
        self.skin = skin or FishSkin()
        self.bubble_system = bubble_system
        self.visible = True
        self.config = config

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

        # Ambient leaf drift cycle (lightweight): configurable burst cadence.
        ambient_cfg = self.config.get("ambient") if self.config and hasattr(self.config, "get") else {}
        if not isinstance(ambient_cfg, dict):
            ambient_cfg = {}

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
        """
        Build a compact plant cluster near the taskbar (bottom right where time/date is).
        Like a real aquarium, plants are grouped together, not spread across the whole tank.
        """
        stems = []
        width = max(240, self.screen_geometry.width())
        height = max(200, self.screen_geometry.height())
        
        # Place plants near bottom right (taskbar area with time/date)
        # In a 1920x1080 screen: taskbar is ~bottom 40px, time is right side
        taskbar_area_width = min(400, width * 0.25)  # Rightmost 25% or 400px
        taskbar_x_start = width - taskbar_area_width - 20  # Start from right side
        
        # 5-6 stems clustered together
        count = 5 if width < 1500 else 6
        cluster_center_x = taskbar_x_start + taskbar_area_width * 0.5
        cluster_spread = min(120, taskbar_area_width * 0.4)  # Tight cluster
        
        for i in range(count):
            # Cluster around center point with small variation
            offset_x = random.uniform(-cluster_spread, cluster_spread)
            # Taller stems in back, shorter in front for depth
            height_bias = (i / max(1, count - 1)) - 0.5  # -0.5 to 0.5
            x_pos = cluster_center_x + offset_x + height_bias * 30
            
            stems.append({
                "x": float(x_pos),
                "phase": random.uniform(0.0, math.pi * 2),
                "sway": random.uniform(6.0, 14.0),
                "thickness": random.uniform(2.4, 4.8),
                "h_mult": random.uniform(0.86, 1.10),
                "style": "broadleaf" if i % 2 == 0 else "feathery",
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
            stem_h = h * 0.90 * growth_ratio * stem["h_mult"]
            top_y = max(waterline, bottom - stem_h)
            x = stem["x"]
            sway = math.sin(t * 0.42 + stem["phase"]) * stem["sway"]

            path = QPainterPath()
            path.moveTo(x, bottom)
            path.cubicTo(
                x + sway * 0.28, bottom - stem_h * 0.33,
                x - sway * 0.75, bottom - stem_h * 0.68,
                x + sway, top_y
            )

            grad = QLinearGradient(x, bottom, x, top_y)
            grad.setColorAt(0.0, QColor(28, 108, 66, 190))
            grad.setColorAt(0.55, QColor(78, 194, 118, 175))
            grad.setColorAt(1.0, QColor(174, 250, 192, 136))
            pen = QPen(QBrush(grad), stem["thickness"])
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawPath(path)

            painter.setPen(Qt.NoPen)
            if stem.get("style") == "broadleaf":
                # Alternate broad leaves like stem plants in real aquariums.
                for i in range(1, 7):
                    fy = bottom - stem_h * (0.18 + i * 0.115)
                    side = -1 if i % 2 == 0 else 1
                    fx = x + side * (5.5 + i * 0.6) + math.sin(t * 0.8 + i + stem["phase"]) * 1.6
                    leaf_w = 10 + i * 0.8
                    leaf_h = 4.8 + i * 0.35
                    painter.setBrush(QColor(138, 236, 156, 105))
                    painter.drawEllipse(QPointF(fx, fy), leaf_w * 0.45, leaf_h)
            else:
                # Feather-like tufts for texture variety.
                painter.setPen(QPen(QColor(146, 235, 164, 88), 0.9))
                for i in range(1, 9):
                    fy = bottom - stem_h * (0.10 + i * 0.09)
                    reach = 5 + i * 1.4
                    bend = math.sin(stem["phase"] + i * 0.8 + t * 0.7) * 2.4
                    painter.drawLine(QPointF(x, fy), QPointF(x + reach + bend, fy - 2.0))
                    painter.drawLine(QPointF(x, fy), QPointF(x - reach + bend * 0.2, fy - 1.6))

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

    def _spawn_leaf_burst(self):
        """Spawn a small realistic batch of leaves from the top of the screen."""
        now = time.time()
        self._leaf_particles = []
        leaf_count = random.randint(self._leaf_burst_min, self._leaf_burst_max)
        w = self.screen_geometry.width()
        h = self.screen_geometry.height()

        for _ in range(leaf_count):
            self._leaf_particles.append({
                "x": random.uniform(w * 0.10, w * 0.90),
                "y": random.uniform(-36.0, -8.0),
                "vx": random.uniform(-9.0, 9.0),
                "vy": random.uniform(22.0, 44.0),
                "rot": random.uniform(0.0, 360.0),
                "spin": random.uniform(-46.0, 46.0),
                "size": random.uniform(6.0, 10.0),
                "alpha": random.uniform(150.0, 210.0),
                "grounded": False,
                "ground_y": h - random.uniform(8.0, 24.0),
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

        # Start a new cycle roughly every 5 minutes when idle.
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
                # subtle floor jitter to look alive while piled/scattered
                leaf["x"] += math.sin(now * 1.9 + leaf["rot"] * 0.02) * 0.08
                leaf["rot"] += math.sin(now * 0.7 + leaf["x"] * 0.01) * 0.2

            # After a short pause, trigger a wind gust that scatters then fades.
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
            painter.drawLine(QPointF(0, -size * 0.82), QPointF(0, size * 0.84))
            painter.restore()

        painter.restore()

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

        # Ambient falling leaves cycle (lightweight).
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
