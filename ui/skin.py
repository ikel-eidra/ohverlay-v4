"""
Realistic Betta Fish renderer using QPainter with Perlin noise-driven fin animation.
Features: multi-layered flowing fins, iridescent color shifting, organic body shape,
breathing glow aura, and realistic eye with mood expression.
"""

import math
import numpy as np
from PySide6.QtGui import (
    QPainter, QColor, QPolygonF, QPen, QRadialGradient,
    QLinearGradient, QPainterPath, QBrush
)
from PySide6.QtCore import QPointF, Qt
from engine.perlin import PerlinNoise


class FishSkin:
    """High-fidelity Betta fish with procedurally animated flowing fins."""

    def __init__(self, config=None):
        self.perlin = PerlinNoise(seed=42)
        self.time = 0.0
        self.tail_phase = 0.0
        self.glow_phase = 0.0
        self.color_shift_phase = 0.0
        self.breath_phase = 0.0

        # Default colors (overridden by config)
        self.primary = [30, 80, 220]
        self.secondary = [180, 40, 120]
        self.accent = [255, 100, 200]
        self.color_shift_speed = 0.3
        self.enable_glow = True
        self.size_scale = 1.0
        self.opacity = 0.9

        if config:
            self.apply_config(config)

    def apply_config(self, config):
        """Update visual parameters from config dict."""
        fish_cfg = config.get("fish") if hasattr(config, "get") and callable(config.get) else {}
        if not fish_cfg:
            return
        if isinstance(fish_cfg, dict):
            self.primary = fish_cfg.get("primary_color", self.primary)
            self.secondary = fish_cfg.get("secondary_color", self.secondary)
            self.accent = fish_cfg.get("accent_color", self.accent)
            self.color_shift_speed = fish_cfg.get("color_shift_speed", self.color_shift_speed)
            self.enable_glow = fish_cfg.get("enable_glow", self.enable_glow)
            self.size_scale = fish_cfg.get("size_scale", self.size_scale)
            self.opacity = fish_cfg.get("opacity", self.opacity)

    def set_colors(self, primary, secondary, accent):
        """Set fish colors directly. Each is [r, g, b]."""
        self.primary = list(primary)
        self.secondary = list(secondary)
        self.accent = list(accent)

    def _lerp_color(self, c1, c2, t):
        """Linearly interpolate between two [r,g,b] colors."""
        t = max(0.0, min(1.0, t))
        return [int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)]

    def _shifted_color(self, base, phase_offset=0.0):
        """Create an iridescent color shift using sine waves."""
        t = (math.sin(self.color_shift_phase + phase_offset) + 1.0) / 2.0
        shifted = self._lerp_color(base, self.secondary, t * 0.4)
        return shifted

    def _make_color(self, rgb, alpha=255):
        """Create QColor from [r,g,b] with alpha."""
        return QColor(rgb[0], rgb[1], rgb[2], int(alpha * self.opacity))

    def render(self, painter, local_pos, fish_state):
        """Render the complete betta fish at local_pos."""
        x, y = local_pos
        vx, vy = fish_state["velocity"]
        speed = math.sqrt(vx * vx + vy * vy)

        if abs(vx) < 0.1 and abs(vy) < 0.1:
            angle = 0
        else:
            angle = math.degrees(math.atan2(vy, vx))

        hunger = fish_state.get("hunger", 0)
        mood = fish_state.get("mood", 100)
        state = fish_state.get("state", "IDLE")

        # Advance animation phases
        dt = 0.033  # ~30 FPS
        speed_factor = min(speed / 150.0, 2.0)
        self.time += dt
        self.tail_phase += (0.12 + 0.08 * speed_factor) * (1.0 + speed_factor)
        self.glow_phase += 0.06
        self.color_shift_phase += self.color_shift_speed * dt
        self.breath_phase += 0.04

        sc = self.size_scale
        flipped = abs(angle) > 90

        painter.save()
        painter.translate(x, y)

        if flipped:
            painter.rotate(angle + 180)
            painter.scale(-sc, sc)
        else:
            painter.rotate(angle)
            painter.scale(sc, sc)

        # --- Render layers (back to front) ---
        self._draw_glow(painter, mood)
        self._draw_caudal_fin(painter, speed_factor)      # Tail fin (behind body)
        self._draw_anal_fin(painter, speed_factor)         # Bottom fin (behind body)
        self._draw_ventral_fins(painter, speed_factor)     # Pelvic fins
        self._draw_body(painter, hunger, mood)
        self._draw_dorsal_fin(painter, speed_factor)       # Top fin (on body)
        self._draw_pectoral_fin(painter, speed_factor)     # Side fin
        self._draw_eye(painter, mood, hunger)
        self._draw_scales_shimmer(painter)

        painter.restore()

    def _draw_glow(self, painter, mood):
        """Ambient glow aura around the fish."""
        if not self.enable_glow:
            return
        glow_size = 55 + math.sin(self.glow_phase) * 12
        breath = math.sin(self.breath_phase) * 0.3 + 0.7
        glow_alpha = int(35 * breath * (mood / 100.0))
        col = self._shifted_color(self.primary, 0.5)

        gradient = QRadialGradient(0, 0, glow_size)
        gradient.setColorAt(0.0, self._make_color(col, glow_alpha))
        gradient.setColorAt(0.5, self._make_color(col, int(glow_alpha * 0.4)))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), glow_size, glow_size * 0.7)

    def _draw_body(self, painter, hunger, mood):
        """Main body: elegant tapered ellipse with gradient shading."""
        col = self._shifted_color(self.primary)
        alpha = int(200 + (mood / 100.0) * 55)

        body_path = QPainterPath()
        # Elegant elongated body shape using cubic bezier
        body_path.moveTo(28, 0)
        body_path.cubicTo(22, -14, -5, -16, -22, -8)
        body_path.cubicTo(-30, -4, -32, 4, -22, 8)
        body_path.cubicTo(-5, 16, 22, 14, 28, 0)

        # Body gradient: lighter belly, darker back
        body_grad = QLinearGradient(0, -16, 0, 16)
        body_grad.setColorAt(0.0, self._make_color(self._lerp_color(col, [255, 255, 255], 0.15), alpha))
        body_grad.setColorAt(0.4, self._make_color(col, alpha))
        body_grad.setColorAt(1.0, self._make_color(self._lerp_color(col, [0, 0, 0], 0.2), alpha))

        painter.setPen(QPen(self._make_color(self._lerp_color(col, [0, 0, 0], 0.3), 80), 0.8))
        painter.setBrush(QBrush(body_grad))
        painter.drawPath(body_path)

    def _draw_caudal_fin(self, painter, speed_factor):
        """Flowing caudal (tail) fin with Perlin noise undulation."""
        num_segments = 18
        fin_length = 55
        fin_spread = 42

        col_top = self._shifted_color(self.accent, 1.0)
        col_bot = self._shifted_color(self.secondary, 2.0)

        # Generate flowing edge points using Perlin noise
        upper_points = [QPointF(-18, -3)]
        lower_points = [QPointF(-18, 3)]

        for i in range(1, num_segments + 1):
            t = i / num_segments
            px = -18 - t * fin_length

            # Perlin noise for organic waviness
            noise_upper = self.perlin.octave_noise(t * 3.0, self.time * 1.5, octaves=2) * 18
            noise_lower = self.perlin.octave_noise(t * 3.0 + 10.0, self.time * 1.5, octaves=2) * 18

            # Sine wave base motion + perlin organic overlay
            wave = math.sin(self.tail_phase - t * 2.5) * (12 + t * 20) * (0.6 + speed_factor * 0.4)

            spread = t * fin_spread
            upper_points.append(QPointF(px, -spread + wave + noise_upper))
            lower_points.append(QPointF(px, spread + wave + noise_lower))

        # Draw filled fin with gradient
        fin_path = QPainterPath()
        fin_path.moveTo(upper_points[0])
        for p in upper_points[1:]:
            fin_path.lineTo(p)
        for p in reversed(lower_points):
            fin_path.lineTo(p)
        fin_path.closeSubpath()

        fin_grad = QLinearGradient(-18, -fin_spread, -18, fin_spread)
        fin_grad.setColorAt(0.0, self._make_color(col_top, 160))
        fin_grad.setColorAt(0.5, self._make_color(self._shifted_color(self.primary, 1.5), 140))
        fin_grad.setColorAt(1.0, self._make_color(col_bot, 160))

        painter.setPen(QPen(self._make_color(col_top, 60), 0.5))
        painter.setBrush(QBrush(fin_grad))
        painter.drawPath(fin_path)

        # Fin ray lines for realism
        painter.setPen(QPen(self._make_color([255, 255, 255], 25), 0.3))
        for i in range(2, num_segments, 3):
            t = i / num_segments
            painter.drawLine(upper_points[0], upper_points[i])
            painter.drawLine(lower_points[0], lower_points[i])

    def _draw_dorsal_fin(self, painter, speed_factor):
        """Tall, flowing dorsal fin along the top of the body."""
        num_pts = 14
        col = self._shifted_color(self.accent, 0.8)

        points = []
        base_start_x = 15
        base_end_x = -20

        for i in range(num_pts + 1):
            t = i / num_pts
            bx = base_start_x + (base_end_x - base_start_x) * t

            # Height envelope: peak in the middle, taper at ends
            envelope = math.sin(t * math.pi) ** 0.7
            base_height = 32 * envelope

            noise = self.perlin.octave_noise(t * 4.0 + 5.0, self.time * 1.2, octaves=2) * 8
            wave = math.sin(self.tail_phase * 0.7 - t * 2.0) * (4 + 6 * speed_factor) * envelope

            points.append(QPointF(bx, -12 - base_height + wave + noise))

        fin_path = QPainterPath()
        fin_path.moveTo(base_start_x, -10)
        for p in points:
            fin_path.lineTo(p)
        fin_path.lineTo(base_end_x, -10)
        fin_path.closeSubpath()

        fin_grad = QLinearGradient(0, -45, 0, -10)
        fin_grad.setColorAt(0.0, self._make_color(col, 100))
        fin_grad.setColorAt(0.6, self._make_color(self._lerp_color(col, self.primary, 0.5), 150))
        fin_grad.setColorAt(1.0, self._make_color(self.primary, 170))

        painter.setPen(QPen(self._make_color(col, 50), 0.4))
        painter.setBrush(QBrush(fin_grad))
        painter.drawPath(fin_path)

        # Fin rays
        painter.setPen(QPen(self._make_color([255, 255, 255], 18), 0.3))
        for i in range(1, num_pts, 2):
            t = i / num_pts
            bx = base_start_x + (base_end_x - base_start_x) * t
            painter.drawLine(QPointF(bx, -10), points[i])

    def _draw_anal_fin(self, painter, speed_factor):
        """Flowing anal fin along the bottom of the body."""
        num_pts = 10
        col = self._shifted_color(self.secondary, 1.5)

        points = []
        base_start_x = 5
        base_end_x = -22

        for i in range(num_pts + 1):
            t = i / num_pts
            bx = base_start_x + (base_end_x - base_start_x) * t

            envelope = math.sin(t * math.pi) ** 0.8
            base_depth = 22 * envelope

            noise = self.perlin.octave_noise(t * 3.5 + 20.0, self.time * 1.3, octaves=2) * 6
            wave = math.sin(self.tail_phase * 0.8 - t * 2.2) * (3 + 5 * speed_factor) * envelope

            points.append(QPointF(bx, 10 + base_depth + wave + noise))

        fin_path = QPainterPath()
        fin_path.moveTo(base_start_x, 8)
        for p in points:
            fin_path.lineTo(p)
        fin_path.lineTo(base_end_x, 8)
        fin_path.closeSubpath()

        fin_grad = QLinearGradient(0, 8, 0, 35)
        fin_grad.setColorAt(0.0, self._make_color(self.primary, 170))
        fin_grad.setColorAt(0.5, self._make_color(self._lerp_color(col, self.primary, 0.4), 140))
        fin_grad.setColorAt(1.0, self._make_color(col, 100))

        painter.setPen(QPen(self._make_color(col, 40), 0.4))
        painter.setBrush(QBrush(fin_grad))
        painter.drawPath(fin_path)

    def _draw_ventral_fins(self, painter, speed_factor):
        """Long, elegant ventral (pelvic) fins that trail below."""
        col = self._shifted_color(self.accent, 2.5)

        for side in [-1, 1]:
            num_pts = 12
            points = [QPointF(5, side * 8)]

            for i in range(1, num_pts + 1):
                t = i / num_pts
                noise = self.perlin.octave_noise(
                    t * 3.0 + side * 30.0, self.time * 1.0 + side * 5.0, octaves=2
                ) * 10
                wave = math.sin(self.tail_phase * 0.6 - t * 1.8 + side * 0.5) * (5 + 8 * speed_factor)

                px = 5 - t * 30
                py = side * (8 + t * 35) + wave + noise

                points.append(QPointF(px, py))

            fin_path = QPainterPath()
            fin_path.moveTo(points[0])
            # Use quadratic curves for smoothness
            for i in range(1, len(points) - 1, 2):
                ctrl = points[i]
                end = points[min(i + 1, len(points) - 1)]
                fin_path.quadTo(ctrl, end)
            if len(points) % 2 == 0:
                fin_path.lineTo(points[-1])

            # Thin trailing shape
            fin_path.lineTo(QPointF(8, side * 6))
            fin_path.closeSubpath()

            alpha_mod = 0.7 + 0.3 * math.sin(self.breath_phase + side)
            painter.setPen(QPen(self._make_color(col, int(30 * alpha_mod)), 0.3))
            painter.setBrush(self._make_color(col, int(110 * alpha_mod)))
            painter.drawPath(fin_path)

    def _draw_pectoral_fin(self, painter, speed_factor):
        """Small pectoral fin on the side of the body."""
        col = self._shifted_color(self.primary, 3.0)

        wave = math.sin(self.tail_phase * 1.2) * 5
        noise = self.perlin.noise2d(self.time * 2.0, 50.0) * 4

        fin_path = QPainterPath()
        fin_path.moveTo(10, 2)
        fin_path.quadTo(QPointF(18, 12 + wave + noise), QPointF(5, 18 + wave))
        fin_path.quadTo(QPointF(2, 10 + wave * 0.5), QPointF(10, 2))

        painter.setPen(QPen(self._make_color(col, 50), 0.4))
        painter.setBrush(self._make_color(col, 100))
        painter.drawPath(fin_path)

    def _draw_eye(self, painter, mood, hunger):
        """Expressive eye with iris, pupil, and highlight."""
        eye_x, eye_y = 18, -3
        eye_r = 4.5

        # Sclera (white)
        painter.setPen(QPen(QColor(80, 80, 80, 200), 0.6))
        painter.setBrush(QColor(240, 240, 245, 230))
        painter.drawEllipse(QPointF(eye_x, eye_y), eye_r, eye_r * 0.9)

        # Iris color: calm = deep blue/violet, stressed = amber/red
        stress = hunger / 100.0
        iris_calm = [20, 30, 80]
        iris_stressed = [180, 60, 20]
        iris_col = self._lerp_color(iris_calm, iris_stressed, stress)

        iris_grad = QRadialGradient(eye_x - 0.5, eye_y - 0.5, eye_r * 0.75)
        iris_grad.setColorAt(0.0, QColor(iris_col[0], iris_col[1], iris_col[2], 255))
        iris_grad.setColorAt(0.7, QColor(
            max(0, iris_col[0] - 30),
            max(0, iris_col[1] - 20),
            max(0, iris_col[2] - 10), 255
        ))
        iris_grad.setColorAt(1.0, QColor(40, 30, 20, 255))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(iris_grad))
        painter.drawEllipse(QPointF(eye_x, eye_y), eye_r * 0.72, eye_r * 0.68)

        # Pupil: dilates when mood is low
        pupil_size = eye_r * (0.28 + 0.12 * (1.0 - mood / 100.0))
        painter.setBrush(QColor(5, 5, 5, 240))
        painter.drawEllipse(QPointF(eye_x, eye_y), pupil_size, pupil_size * 0.9)

        # Specular highlight
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(QPointF(eye_x + 1.5, eye_y - 1.5), 1.2, 1.0)

    def _draw_scales_shimmer(self, painter):
        """Subtle scale-like shimmer overlay on the body."""
        shimmer_alpha = int(15 + 10 * math.sin(self.time * 2.0))
        painter.setPen(Qt.NoPen)

        for row in range(3):
            for col in range(6):
                sx = 20 - col * 8
                sy = -8 + row * 8
                offset = self.perlin.noise2d(col * 0.5 + self.time * 0.5, row * 0.5) * 3
                a = max(0, min(255, shimmer_alpha + int(offset * 5)))
                painter.setBrush(QColor(255, 255, 255, a))
                painter.drawEllipse(QPointF(sx + offset, sy + offset * 0.5), 3, 2.2)
