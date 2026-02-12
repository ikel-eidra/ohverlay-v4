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

        # Procedural plant bed (grows over 3 days, then resets - daily growth cycle).
        self._plant_cycle_start = time.time()
        self._plant_grow_days = 3  # Full growth over 3 days
        self._plant_grow_seconds = self._plant_grow_days * 24 * 60 * 60
        self._plant_stems = self._build_plant_layout()
        self._taskbar_height = 40  # Standard Windows taskbar height

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
        Build needle-leaf plant cluster starting from taskbar TOP edge.
        Plants grow UPWARD over days, cycling back when reaching max height.
        Positioned so they don't cover Windows time/taskbar icons.
        """
        stems = []
        width = max(240, self.screen_geometry.width())
        height = self.screen_geometry.height()
        
        # Position at bottom right but starting from TASKBAR TOP
        # Taskbar is ~40px, so plants start at height - 40 and grow UP
        taskbar_area_width = min(400, width * 0.25)
        taskbar_x_start = width - taskbar_area_width - 20
        taskbar_top_y = height - self._taskbar_height  # Start here, grow upward
        
        # 5-7 needle-leaf plants
        count = 5 if width < 1500 else 7
        cluster_center_x = taskbar_x_start + taskbar_area_width * 0.5
        cluster_spread = min(130, taskbar_area_width * 0.42)
        
        for i in range(count):
            offset_x = random.uniform(-cluster_spread, cluster_spread)
            # Each plant has different growth characteristics
            growth_speed = random.uniform(0.8, 1.2)  # Variation in growth
            max_height_factor = random.uniform(0.7, 1.0)  # Different max heights
            
            x_pos = cluster_center_x + offset_x
            
            stems.append({
                "x": float(x_pos),
                "base_y": float(taskbar_top_y),  # Start at taskbar top
                "phase": random.uniform(0.0, math.pi * 2),
                "sway": random.uniform(3.0, 8.0),
                "growth_speed": growth_speed,
                "max_height_factor": max_height_factor,
                "needle_density": random.randint(8, 14),  # Number of needle leaves
            })
        return stems

    def _plant_height_ratio(self):
        """
        Calculate plant growth over days.
        Returns 0.0 to 1.0 representing growth progress.
        When fully grown, cycle resets to start growth again.
        """
        elapsed = max(0.0, time.time() - self._plant_cycle_start)
        
        # Reset cycle when fully grown (after 3 days)
        if elapsed >= self._plant_grow_seconds:
            self._plant_cycle_start = time.time()
            elapsed = 0.0
            logger.info("Plant growth cycle complete! Restarting from small sprouts...")
        
        # Growth curve: slow start, faster middle, slow end (sigmoid-like)
        grow_t = elapsed / self._plant_grow_seconds
        # Smooth growth curve
        smooth_t = grow_t * grow_t * (3 - 2 * grow_t)  # Smoothstep
        return smooth_t

    def _draw_plants(self, painter):
        """
        Draw needle-leaf plants growing UPWARD from taskbar.
        Cryptocoryne-style with tiny needle leaves.
        Grows over days, cycling when reaching max height.
        """
        if not self._plant_stems:
            return
        
        growth_ratio = self._plant_height_ratio()
        t = time.time()
        
        for stem in self._plant_stems:
            base_x = stem["x"]
            base_y = stem["base_y"]
            
            # Current height based on growth cycle
            max_height = 150 * stem["max_height_factor"] * stem["growth_speed"]
            current_height = max_height * growth_ratio
            
            # Minimum visible height (small sprouts)
            if current_height < 15:
                current_height = 15 * growth_ratio  # Tiny sprouts emerging
            
            # Plant sway
            sway = math.sin(t * 0.3 + stem["phase"]) * stem["sway"] * (0.5 + growth_ratio * 0.5)
            
            # Draw needle-leaf plant
            self._draw_needle_plant(painter, base_x, base_y, current_height, sway, t, stem, growth_ratio)

    def _draw_needle_plant(self, painter, base_x, base_y, height, sway, t, stem, growth_ratio):
        """
        Cryptocoryne-style needle leaf plants.
        Tiny needle leaves growing UPWARD from base.
        Like aquatic moss or fine-leaf Cryptocoryne.
        """
        # Crown/base at taskbar top
        crown_size = 6 + growth_ratio * 4
        
        # Draw crown
        painter.setPen(Qt.NoPen)
        crown_grad = QRadialGradient(base_x, base_y, crown_size)
        crown_grad.setColorAt(0.0, QColor(40, 95, 40, 180))
        crown_grad.setColorAt(1.0, QColor(25, 65, 25, 120))
        painter.setBrush(QBrush(crown_grad))
        painter.drawEllipse(QPointF(base_x, base_y), crown_size, crown_size * 0.5)
        
        # Number of needle leaves based on growth
        num_leaves = int(stem["needle_density"] * growth_ratio)
        if num_leaves < 3:
            num_leaves = 3  # Minimum visible leaves
        
        for i in range(num_leaves):
            # Each leaf radiates from crown
            angle = -90 + (i / max(1, num_leaves - 1) - 0.5) * 60  # Fan upward
            angle += math.sin(t * 0.4 + i * 0.8 + stem["phase"]) * 5  # Sway
            angle_rad = math.radians(angle)
            
            # Leaf length varies (center taller, sides shorter)
            height_factor = 1.0 - abs(i / max(1, num_leaves - 1) - 0.5) * 0.3
            leaf_length = height * height_factor
            
            # Leaf curves outward then up
            mid_x = base_x + math.cos(angle_rad + 0.2) * leaf_length * 0.4 + sway * 0.3
            mid_y = base_y - leaf_length * 0.3
            tip_x = base_x + math.cos(angle_rad) * leaf_length * 0.3 + sway
            tip_y = base_y - leaf_length
            
            # Needle leaf - thin and pointed
            # Draw as thin tapering line
            segments = 8
            points_left = []
            points_right = []
            
            for seg in range(segments + 1):
                seg_t = seg / segments
                
                # Bezier curve for leaf shape
                if seg_t < 0.4:
                    # Curve outward
                    bx = base_x + (mid_x - base_x) * (seg_t / 0.4)
                    by = base_y + (mid_y - base_y) * (seg_t / 0.4)
                else:
                    # Curve up to tip
                    t2 = (seg_t - 0.4) / 0.6
                    bx = mid_x + (tip_x - mid_x) * t2
                    by = mid_y + (tip_y - mid_y) * t2
                
                # Needle width tapers from base to tip
                max_width = 3 * (1 - seg_t * 0.9)  # Very thin
                perp_angle = angle_rad + math.pi / 2
                
                wx = math.cos(perp_angle) * max_width
                wy = math.sin(perp_angle) * max_width
                
                points_left.append((bx - wx, by - wy))
                points_right.append((bx + wx, by + wy))
            
            # Draw needle leaf shape
            leaf_path = QPainterPath()
            leaf_path.moveTo(base_x, base_y)
            
            for lx, ly in points_left:
                leaf_path.lineTo(lx, ly)
            
            leaf_path.lineTo(tip_x, tip_y)
            
            for lx, ly in reversed(points_right):
                leaf_path.lineTo(lx, ly)
            
            leaf_path.closeSubpath()
            
            # Needle leaf color gradient
            leaf_grad = QLinearGradient(base_x, base_y, tip_x, tip_y)
            # Darker at base, lighter at tip
            alpha = int(160 + 40 * growth_ratio)
            leaf_grad.setColorAt(0.0, QColor(30, 80, 35, alpha))
            leaf_grad.setColorAt(0.5, QColor(50, 120, 55, int(alpha * 0.9)))
            leaf_grad.setColorAt(1.0, QColor(70, 150, 75, int(alpha * 0.7)))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(leaf_grad))
            painter.drawPath(leaf_path)
            
            # Central vein
            painter.setPen(QPen(QColor(20, 60, 25, 100), 0.5))
            painter.drawLine(int(base_x), int(base_y), int(tip_x), int(tip_y))
        
        # Add tiny sprouts around base if growing
        if growth_ratio < 0.3:
            # Small emerging sprouts
            for s in range(5):
                sprout_angle = -90 + (s - 2) * 15
                sprout_rad = math.radians(sprout_angle)
                sprout_len = 8 + growth_ratio * 20
                sx = base_x + math.cos(sprout_rad) * sprout_len * 0.3
                sy = base_y - sprout_len
                
                painter.setPen(QPen(QColor(45, 110, 50, int(120 * growth_ratio)), 1))
                painter.drawLine(int(base_x), int(base_y), int(sx), int(sy))

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
