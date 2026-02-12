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
        Build a realistic plant cluster near the taskbar (bottom right where time/date is).
        Mix of Java Fern, Anubias, and Cryptocoryne for authentic aquascape look.
        """
        stems = []
        width = max(240, self.screen_geometry.width())
        
        # Place plants near bottom right (taskbar area)
        taskbar_area_width = min(450, width * 0.28)
        taskbar_x_start = width - taskbar_area_width - 30
        
        # 6-8 plants in natural cluster
        count = 6 if width < 1500 else 8
        cluster_center_x = taskbar_x_start + taskbar_area_width * 0.5
        cluster_spread = min(140, taskbar_area_width * 0.45)
        
        # Plant types for variety
        plant_types = ["java_fern", "anubias", "crypt", "java_fern", "crypt", "anubias"]
        
        for i in range(count):
            offset_x = random.uniform(-cluster_spread, cluster_spread)
            # Back plants taller, front plants shorter
            depth_factor = random.uniform(0.7, 1.15)
            x_pos = cluster_center_x + offset_x
            
            stems.append({
                "x": float(x_pos),
                "phase": random.uniform(0.0, math.pi * 2),
                "sway": random.uniform(4.0, 10.0),
                "thickness": random.uniform(2.0, 4.0),
                "h_mult": depth_factor,
                "plant_type": plant_types[i % len(plant_types)],
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
        """
        Draw realistic aquatic plants (Java Fern, Anubias, Cryptocoryne style).
        Features:
        - Rhizome/base structure
        - Individual leaves with proper shapes
        - Leaf veins and midribs
        - Gentle swaying motion
        - Multiple plant types in cluster
        """
        if not self._plant_stems:
            return
        h = self.screen_geometry.height()
        bottom = h + 5
        growth_ratio = self._plant_height_ratio()
        t = time.time()

        for stem in self._plant_stems:
            plant_height = h * 0.75 * growth_ratio * stem["h_mult"]
            base_x = stem["x"]
            
            # Plant sway based on current
            sway = math.sin(t * 0.35 + stem["phase"]) * stem["sway"] * 0.5
            
            # Draw based on plant type
            plant_type = stem.get("plant_type", "java_fern")
            
            if plant_type == "java_fern":
                self._draw_java_fern(painter, base_x, bottom, plant_height, sway, t, stem)
            elif plant_type == "anubias":
                self._draw_anubias(painter, base_x, bottom, plant_height, sway, t, stem)
            elif plant_type == "crypt":
                self._draw_cryptocoryne(painter, base_x, bottom, plant_height, sway, t, stem)
            else:
                self._draw_java_fern(painter, base_x, bottom, plant_height, sway, t, stem)

    def _draw_java_fern(self, painter, base_x, bottom, height, sway, t, stem):
        """
        Java Fern style - long stem with pointed, serrated leaves.
        Leaves grow from rhizome with irregular spacing.
        """
        # Rhizome (horizontal base)
        rhizome_y = bottom - 15
        rhizome_path = QPainterPath()
        rhizome_path.moveTo(base_x - 20, rhizome_y)
        rhizome_path.quadTo(base_x, rhizome_y - 5, base_x + 20, rhizome_y)
        
        painter.setPen(QPen(QColor(45, 95, 45, 180), 3))
        painter.drawPath(rhizome_path)
        
        # Draw 5-7 leaves per plant
        num_leaves = 5 + int(stem["h_mult"] * 2)
        for i in range(num_leaves):
            # Leaf attachment point on rhizome
            attach_t = (i / max(1, num_leaves - 1)) * 2 - 1  # -1 to 1
            attach_x = base_x + attach_t * 18
            attach_y = rhizome_y - 3
            
            # Leaf growth direction
            angle = -90 + attach_t * 45 + math.sin(t * 0.5 + i + stem["phase"]) * 5
            angle_rad = math.radians(angle)
            
            # Leaf dimensions
            leaf_length = (height * 0.4) * (0.7 + 0.3 * math.sin(i * 1.3))
            leaf_width = 12 + 6 * math.sin(i * 0.7)
            
            # Calculate leaf tip with sway
            tip_x = attach_x + math.cos(angle_rad) * leaf_length + sway * (1 + i * 0.2)
            tip_y = attach_y + math.sin(angle_rad) * leaf_length
            
            # Leaf shape - pointed with serrated edges
            leaf_path = QPainterPath()
            leaf_path.moveTo(attach_x, attach_y)
            
            # Left side with serrations
            for j in range(1, 8):
                seg_t = j / 8
                lx = attach_x + (tip_x - attach_x) * seg_t
                ly = attach_y + (tip_y - attach_y) * seg_t
                # Serrated edge
                serration = math.sin(j * 2.5) * 2 * (1 - seg_t)
                offset_x = -math.sin(angle_rad) * (leaf_width * 0.5 * (1 - seg_t * 0.3) + serration)
                offset_y = math.cos(angle_rad) * (leaf_width * 0.5 * (1 - seg_t * 0.3) + serration)
                if j == 1:
                    leaf_path.lineTo(lx + offset_x, ly + offset_y)
                else:
                    leaf_path.quadTo(lx + offset_x * 0.5, ly + offset_y * 0.5, lx + offset_x, ly + offset_y)
            
            # Tip
            leaf_path.lineTo(tip_x, tip_y)
            
            # Right side
            for j in range(7, 0, -1):
                seg_t = j / 8
                lx = attach_x + (tip_x - attach_x) * seg_t
                ly = attach_y + (tip_y - attach_y) * seg_t
                serration = math.sin(j * 2.5 + math.pi) * 2 * (1 - seg_t)
                offset_x = math.sin(angle_rad) * (leaf_width * 0.5 * (1 - seg_t * 0.3) + serration)
                offset_y = -math.cos(angle_rad) * (leaf_width * 0.5 * (1 - seg_t * 0.3) + serration)
                leaf_path.quadTo(lx + offset_x * 0.5, ly + offset_y * 0.5, lx + offset_x, ly + offset_y)
            
            leaf_path.closeSubpath()
            
            # Leaf gradient
            leaf_grad = QLinearGradient(attach_x, attach_y, tip_x, tip_y)
            leaf_grad.setColorAt(0.0, QColor(35, 85, 35, 200))
            leaf_grad.setColorAt(0.5, QColor(55, 130, 55, 180))
            leaf_grad.setColorAt(1.0, QColor(75, 160, 75, 160))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(leaf_grad))
            painter.drawPath(leaf_path)
            
            # Central vein (midrib)
            painter.setPen(QPen(QColor(25, 70, 25, 120), 1.2))
            painter.drawLine(int(attach_x), int(attach_y), int(tip_x), int(tip_y))

    def _draw_anubias(self, painter, base_x, bottom, height, sway, t, stem):
        """
        Anubias style - broad, oval leaves on long petioles.
        Dark green, thick, waxy appearance.
        """
        # Rhizome
        rhizome_y = bottom - 12
        painter.setPen(QPen(QColor(35, 75, 35, 200), 4))
        painter.drawLine(int(base_x - 15), int(rhizome_y), int(base_x + 15), int(rhizome_y))
        
        # Draw 4-6 broad leaves
        num_leaves = 4 + int(stem["h_mult"] * 2)
        for i in range(num_leaves):
            # Petiole (leaf stem)
            attach_t = (i / max(1, num_leaves - 1)) * 1.6 - 0.8
            attach_x = base_x + attach_t * 12
            
            # Petiole angle
            angle = -80 + attach_t * 30 + math.sin(t * 0.4 + i * 1.2) * 3
            angle_rad = math.radians(angle)
            
            petiole_length = height * 0.35
            leaf_base_x = attach_x + math.cos(angle_rad) * petiole_length + sway * 0.5
            leaf_base_y = rhizome_y + math.sin(angle_rad) * petiole_length
            
            # Draw petiole
            painter.setPen(QPen(QColor(40, 90, 40, 160), 2))
            painter.drawLine(int(attach_x), int(rhizome_y - 3), int(leaf_base_x), int(leaf_base_y))
            
            # Leaf blade - oval shape
            leaf_length = height * 0.35
            leaf_width = height * 0.22
            
            # Leaf points
            tip_x = leaf_base_x + math.cos(angle_rad) * leaf_length
            tip_y = leaf_base_y + math.sin(angle_rad) * leaf_length
            
            # Create oval leaf shape
            leaf_path = QPainterPath()
            leaf_path.moveTo(leaf_base_x, leaf_base_y)
            
            # Left curve
            ctrl1_x = leaf_base_x - math.sin(angle_rad) * leaf_width * 0.6
            ctrl1_y = leaf_base_y + math.cos(angle_rad) * leaf_width * 0.6
            ctrl2_x = tip_x - math.sin(angle_rad) * leaf_width * 0.3
            ctrl2_y = tip_y + math.cos(angle_rad) * leaf_width * 0.3
            leaf_path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, tip_x, tip_y)
            
            # Right curve
            ctrl3_x = tip_x + math.sin(angle_rad) * leaf_width * 0.3
            ctrl3_y = tip_y - math.cos(angle_rad) * leaf_width * 0.3
            ctrl4_x = leaf_base_x + math.sin(angle_rad) * leaf_width * 0.6
            ctrl4_y = leaf_base_y - math.cos(angle_rad) * leaf_width * 0.6
            leaf_path.cubicTo(ctrl3_x, ctrl3_y, ctrl4_x, ctrl4_y, leaf_base_x, leaf_base_y)
            
            # Dark green waxy gradient
            leaf_grad = QRadialGradient(leaf_base_x + (tip_x - leaf_base_x) * 0.4, 
                                       leaf_base_y + (tip_y - leaf_base_y) * 0.4, 
                                       leaf_length * 0.6)
            leaf_grad.setColorAt(0.0, QColor(45, 105, 45, 220))
            leaf_grad.setColorAt(0.6, QColor(35, 85, 35, 200))
            leaf_grad.setColorAt(1.0, QColor(25, 65, 25, 180))
            
            painter.setPen(QPen(QColor(20, 60, 20, 100), 0.8))
            painter.setBrush(QBrush(leaf_grad))
            painter.drawPath(leaf_path)
            
            # Midrib and veins
            painter.setPen(QPen(QColor(60, 130, 60, 150), 1.5))
            painter.drawLine(int(leaf_base_x), int(leaf_base_y), int(tip_x), int(tip_y))
            
            # Lateral veins
            for v in range(3, 8):
                vt = v / 10
                vx = leaf_base_x + (tip_x - leaf_base_x) * vt
                vy = leaf_base_y + (tip_y - leaf_base_y) * vt
                vein_len = leaf_width * 0.4 * (1 - abs(vt - 0.5))
                painter.setPen(QPen(QColor(50, 110, 50, 100), 0.6))
                painter.drawLine(int(vx), int(vy), int(vx - math.sin(angle_rad) * vein_len), 
                               int(vy + math.cos(angle_rad) * vein_len))
                painter.drawLine(int(vx), int(vy), int(vx + math.sin(angle_rad) * vein_len), 
                               int(vy - math.cos(angle_rad) * vein_len))

    def _draw_cryptocoryne(self, painter, base_x, bottom, height, sway, t, stem):
        """
        Cryptocoryne style - rosette of ruffled, textured leaves.
        Shorter, bushier growth form.
        """
        # Crown/base
        crown_y = bottom - 10
        crown_size = 8 + stem["h_mult"] * 4
        
        painter.setPen(Qt.NoPen)
        crown_grad = QRadialGradient(base_x, crown_y, crown_size)
        crown_grad.setColorAt(0.0, QColor(55, 120, 55, 200))
        crown_grad.setColorAt(1.0, QColor(35, 80, 35, 150))
        painter.setBrush(QBrush(crown_grad))
        painter.drawEllipse(QPointF(base_x, crown_y), crown_size, crown_size * 0.6)
        
        # Rosette of 6-10 leaves
        num_leaves = 6 + int(stem["h_mult"] * 3)
        for i in range(num_leaves):
            # Leaves arranged in spiral/rosette
            angle = (i / num_leaves) * 360 + math.sin(t * 0.3 + i) * 5
            angle_rad = math.radians(angle)
            
            # Varying leaf sizes (inner smaller, outer larger)
            size_factor = 0.5 + (i / num_leaves) * 0.5
            leaf_length = height * 0.3 * size_factor
            leaf_width = height * 0.18 * size_factor
            
            # Leaf base
            leaf_base_x = base_x + math.cos(angle_rad) * 5
            leaf_base_y = crown_y + math.sin(angle_rad) * 3
            
            # Leaf tip with sway
            tip_x = leaf_base_x + math.cos(angle_rad) * leaf_length + sway * 0.3
            tip_y = leaf_base_y + math.sin(angle_rad) * leaf_length
            
            # Ruffled leaf shape (crypts have wavy edges)
            leaf_path = QPainterPath()
            leaf_path.moveTo(leaf_base_x, leaf_base_y)
            
            # Left side with ruffles
            points_left = []
            for j in range(6):
                seg_t = (j + 1) / 6
                lx = leaf_base_x + (tip_x - leaf_base_x) * seg_t
                ly = leaf_base_y + (tip_y - leaf_base_y) * seg_t
                # Ruffle effect
                ruffle = math.sin(j * 1.8 + t * 0.5) * 3 * (1 - seg_t * 0.5)
                offset_x = -math.sin(angle_rad) * (leaf_width * 0.5 * math.sin(seg_t * math.pi) + ruffle)
                offset_y = math.cos(angle_rad) * (leaf_width * 0.5 * math.sin(seg_t * math.pi) + ruffle)
                points_left.append((lx + offset_x, ly + offset_y))
            
            for px, py in points_left:
                leaf_path.lineTo(px, py)
            
            # Tip
            leaf_path.lineTo(tip_x, tip_y)
            
            # Right side
            for j in range(5, -1, -1):
                seg_t = (j + 1) / 6
                lx = leaf_base_x + (tip_x - leaf_base_x) * seg_t
                ly = leaf_base_y + (tip_y - leaf_base_y) * seg_t
                ruffle = math.sin(j * 1.8 + math.pi + t * 0.5) * 3 * (1 - seg_t * 0.5)
                offset_x = math.sin(angle_rad) * (leaf_width * 0.5 * math.sin(seg_t * math.pi) + ruffle)
                offset_y = -math.cos(angle_rad) * (leaf_width * 0.5 * math.sin(seg_t * math.pi) + ruffle)
                leaf_path.lineTo(lx + offset_x, ly + offset_y)
            
            leaf_path.closeSubpath()
            
            # Textured green gradient
            leaf_grad = QLinearGradient(leaf_base_x, leaf_base_y, tip_x, tip_y)
            leaf_grad.setColorAt(0.0, QColor(50, 115, 50, 210))
            leaf_grad.setColorAt(0.4, QColor(65, 140, 65, 190))
            leaf_grad.setColorAt(1.0, QColor(80, 160, 80, 170))
            
            painter.setPen(QPen(QColor(30, 80, 30, 80), 0.6))
            painter.setBrush(QBrush(leaf_grad))
            painter.drawPath(leaf_path)
            
            # Texture lines (crypt veins)
            painter.setPen(QPen(QColor(70, 130, 70, 100), 0.8))
            for v in range(2, 5):
                vt = v / 6
                vx = leaf_base_x + (tip_x - leaf_base_x) * vt
                vy = leaf_base_y + (tip_y - leaf_base_y) * vt
                # Short texture marks
                mark_len = 4 * (1 - vt)
                painter.drawLine(int(vx - math.sin(angle_rad) * mark_len), int(vy + math.cos(angle_rad) * mark_len),
                               int(vx + math.sin(angle_rad) * mark_len), int(vy - math.cos(angle_rad) * mark_len))

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
