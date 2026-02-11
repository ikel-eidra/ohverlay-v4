"""
Realistic Neon Tetra renderer.
Small torpedo-shaped fish with the iconic iridescent blue-green stripe
and bright red tail section. Translucent body, tiny delicate fins.
Designed for schooling - looks best in groups of 6-12.
"""

import math
from PySide6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient,
    QLinearGradient, QPainterPath, QBrush
)
from PySide6.QtCore import QPointF, Qt
from engine.perlin import PerlinNoise


class NeonTetraSkin:
    """Photorealistic neon tetra with iridescent stripe and translucent body."""

    def __init__(self, seed=42):
        self.perlin = PerlinNoise(seed=seed)
        self.time = 0.0
        self.tail_phase = 0.0
        self.breath_phase = 0.0
        self.shimmer_phase = 0.0

        # Each fish gets slight color variation
        self._hue_offset = (((seed * 97) % 360) / 360.0 - 0.5) * 0.12
        self.size_scale = 1.0
        self.opacity = 0.92
        self._facing_left = False

    def set_colors(self, primary, secondary, accent):
        """Compatibility with tray color picker - tints the stripe."""
        pass  # Neon tetras have fixed coloring

    def apply_config(self, config):
        fish_cfg = config.get("fish") if hasattr(config, "get") and callable(config.get) else {}
        if isinstance(fish_cfg, dict):
            raw_scale = fish_cfg.get("size_scale", self.size_scale)
            try:
                self.size_scale = max(0.2, min(3.0, float(raw_scale)))
            except (TypeError, ValueError):
                pass

    def render(self, painter, local_pos, fish_state):
        x, y = local_pos
        vx, vy = fish_state["velocity"]
        speed = math.sqrt(vx * vx + vy * vy)

        if abs(vx) < 0.1 and abs(vy) < 0.1:
            angle = fish_state.get("facing_angle", 0)
            angle = math.degrees(angle)
        else:
            angle = math.degrees(math.atan2(vy, vx))

        dt = 0.033
        speed_factor = min(speed / 100.0, 2.0)
        self.time += dt
        self.tail_phase += (0.15 + 0.12 * speed_factor) * (1.0 + speed_factor)
        self.breath_phase += 0.04
        self.shimmer_phase += 0.08

        sc = self.size_scale * 0.72  # More realistic desktop-visible size
        if vx < -2.0:
            self._facing_left = True
        elif vx > 2.0:
            self._facing_left = False
        flipped = self._facing_left

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(x, y)

        if flipped:
            painter.rotate(angle + 180)
            painter.scale(-sc, sc)
        else:
            painter.rotate(angle)
            painter.scale(sc, sc)

        self._draw_tail_fin(painter, speed_factor)
        self._draw_anal_fin(painter, speed_factor)
        self._draw_body(painter, speed_factor)
        self._draw_neon_stripe(painter)
        self._draw_red_section(painter)
        self._draw_dorsal_fin(painter, speed_factor)
        self._draw_eye(painter)
        self._draw_body_highlight(painter)

        painter.restore()

    def _draw_body(self, painter, speed_factor):
        """Translucent torpedo body with silver belly."""
        flex = math.sin(self.tail_phase * 0.5) * 2.0 * speed_factor

        body = QPainterPath()
        body.moveTo(22, 0)  # Nose
        # Upper
        body.cubicTo(18, -5 + flex * 0.2, 6, -8 + flex * 0.4, -6, -7 + flex * 0.3)
        body.cubicTo(-14, -6, -20, -4, -24, -2)
        # Peduncle
        body.cubicTo(-26, -1, -27, 0, -26, 1)
        # Lower
        body.cubicTo(-24, 3, -20, 5, -14, 6)
        body.cubicTo(-6, 7 - flex * 0.3, 6, 8 - flex * 0.4, 18, 5 - flex * 0.2)
        body.cubicTo(20, 3, 22, 1, 22, 0)

        # Translucent silver body gradient
        grad = QLinearGradient(0, -9, 0, 9)
        grad.setColorAt(0.0, QColor(140, 160, 170, int(180 * self.opacity)))
        grad.setColorAt(0.3, QColor(180, 195, 205, int(200 * self.opacity)))
        grad.setColorAt(0.5, QColor(200, 215, 225, int(210 * self.opacity)))
        grad.setColorAt(0.8, QColor(220, 225, 230, int(190 * self.opacity)))
        grad.setColorAt(1.0, QColor(240, 240, 245, int(170 * self.opacity)))

        painter.setPen(QPen(QColor(100, 110, 120, 80), 0.4))
        painter.setBrush(QBrush(grad))
        painter.drawPath(body)

    def _draw_neon_stripe(self, painter):
        """The iconic electric blue-green iridescent stripe."""
        shimmer = math.sin(self.shimmer_phase) * 0.15

        stripe = QPainterPath()
        stripe.moveTo(18, -2)
        stripe.cubicTo(10, -3.5, -2, -4, -14, -3)
        stripe.cubicTo(-18, -2.5, -22, -2, -24, -1.5)
        # Return path (bottom of stripe)
        stripe.cubicTo(-22, 0, -18, 0.5, -14, 0)
        stripe.cubicTo(-2, -0.5, 10, -1, 18, -0.5)
        stripe.closeSubpath()

        # Iridescent blue-green gradient that shifts
        hue_shift = self._hue_offset
        r_base = max(0, min(255, int(20 + shimmer * 30 + hue_shift * 90)))
        g_base = max(0, min(255, int(180 + shimmer * 40 + hue_shift * 30)))
        b_base = max(0, min(255, int(255 - shimmer * 20 - hue_shift * 60)))

        stripe_grad = QLinearGradient(18, 0, -24, 0)
        stripe_grad.setColorAt(0.0, QColor(r_base, g_base, b_base, int(230 * self.opacity)))
        stripe_grad.setColorAt(0.3, QColor(
            max(0, r_base - 10), min(255, g_base + 20), b_base, int(250 * self.opacity)))
        stripe_grad.setColorAt(0.6, QColor(
            r_base, min(255, g_base + 30), min(255, b_base + 10), int(240 * self.opacity)))
        stripe_grad.setColorAt(1.0, QColor(
            max(0, r_base - 5), g_base, min(255, b_base + 5), int(200 * self.opacity)))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(stripe_grad))
        painter.drawPath(stripe)

        # Bright glow center
        glow = QPainterPath()
        glow.moveTo(16, -1.5)
        glow.cubicTo(8, -2.5, -4, -2.8, -16, -2)
        glow.cubicTo(-4, -1.2, 8, -1, 16, -1)
        glow.closeSubpath()

        painter.setBrush(QColor(100, 240, 255, int(80 * self.opacity)))
        painter.drawPath(glow)

    def _draw_red_section(self, painter):
        """Bright red rear body section (behind the stripe, into tail)."""
        red = QPainterPath()
        red.moveTo(-14, -3)
        red.cubicTo(-18, -4, -22, -3, -25, -1.5)
        red.cubicTo(-26, 0, -25, 1.5, -22, 3)
        red.cubicTo(-18, 4, -14, 3, -14, 0)
        red.closeSubpath()

        # Vibrant red gradient
        grad = QLinearGradient(-14, 0, -26, 0)
        grad.setColorAt(0.0, QColor(220, 40, 30, int(200 * self.opacity)))
        grad.setColorAt(0.5, QColor(240, 50, 35, int(220 * self.opacity)))
        grad.setColorAt(1.0, QColor(200, 30, 25, int(180 * self.opacity)))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(red)

    def _draw_tail_fin(self, painter, speed_factor):
        """Small forked caudal fin."""
        wave = math.sin(self.tail_phase) * (5 + 8 * speed_factor)
        noise = self.perlin.noise2d(self.time * 1.5, 0) * 3

        fin = QPainterPath()
        fin.moveTo(-24, -1.5)
        # Upper fork
        fin.cubicTo(-28, -4 + wave * 0.5, -32, -8 + wave + noise, -35, -6 + wave)
        fin.cubicTo(-33, -3 + wave * 0.5, -30, -1, -26, 0)
        # Lower fork
        fin.cubicTo(-30, 1, -33, 3 + wave * 0.5, -35, 6 + wave)
        fin.cubicTo(-32, 8 + wave + noise, -28, 4 + wave * 0.5, -24, 1.5)
        fin.closeSubpath()

        grad = QLinearGradient(-24, 0, -35, 0)
        grad.setColorAt(0.0, QColor(230, 50, 40, int(180 * self.opacity)))
        grad.setColorAt(0.5, QColor(240, 60, 45, int(140 * self.opacity)))
        grad.setColorAt(1.0, QColor(220, 40, 35, int(80 * self.opacity)))

        painter.setPen(QPen(QColor(200, 40, 30, 40), 0.3))
        painter.setBrush(QBrush(grad))
        painter.drawPath(fin)

    def _draw_dorsal_fin(self, painter, speed_factor):
        """Tiny translucent dorsal fin."""
        wave = math.sin(self.tail_phase * 0.8) * 2 * speed_factor

        fin = QPainterPath()
        fin.moveTo(4, -7)
        fin.cubicTo(2, -12 + wave, -4, -13 + wave, -8, -7)
        fin.closeSubpath()

        painter.setPen(QPen(QColor(160, 180, 190, 40), 0.2))
        painter.setBrush(QColor(180, 200, 210, int(60 * self.opacity)))
        painter.drawPath(fin)

    def _draw_anal_fin(self, painter, speed_factor):
        """Small anal fin."""
        wave = math.sin(self.tail_phase * 0.7 + 0.5) * 2 * speed_factor

        fin = QPainterPath()
        fin.moveTo(-4, 6)
        fin.cubicTo(-6, 10 + wave, -12, 11 + wave, -16, 6)
        fin.closeSubpath()

        painter.setPen(QPen(QColor(160, 180, 190, 35), 0.2))
        painter.setBrush(QColor(190, 205, 215, int(55 * self.opacity)))
        painter.drawPath(fin)

    def _draw_eye(self, painter):
        """Small bright eye with blue-green reflection."""
        ex, ey = 18, -1.5
        r = 2.5

        # Dark ring
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(30, 30, 40, 180))
        painter.drawEllipse(QPointF(ex, ey), r + 0.4, r * 0.9 + 0.3)

        # Sclera
        painter.setBrush(QColor(240, 245, 248, 230))
        painter.drawEllipse(QPointF(ex, ey), r, r * 0.85)

        # Iris - dark with blue tint
        iris_grad = QRadialGradient(ex, ey, r * 0.7)
        iris_grad.setColorAt(0.0, QColor(20, 40, 60, 255))
        iris_grad.setColorAt(0.7, QColor(10, 20, 35, 255))
        iris_grad.setColorAt(1.0, QColor(5, 10, 15, 255))
        painter.setBrush(QBrush(iris_grad))
        painter.drawEllipse(QPointF(ex, ey), r * 0.65, r * 0.6)

        # Pupil
        painter.setBrush(QColor(2, 2, 2, 250))
        painter.drawEllipse(QPointF(ex, ey), r * 0.3, r * 0.28)

        # Highlight
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(QPointF(ex + 0.8, ey - 0.8), 0.7, 0.6)

    def _draw_body_highlight(self, painter):
        """Wet highlight along upper body."""
        h = QPainterPath()
        h.moveTo(16, -3.5)
        h.cubicTo(8, -5.5, -2, -5.8, -10, -5)
        h.cubicTo(-2, -4.5, 8, -4, 16, -3.5)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 35))
        painter.drawPath(h)
