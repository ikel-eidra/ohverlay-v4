"""
Realistic Discus Fish renderer.
Large, round, laterally compressed body with vibrant vertical bar patterns,
flowing dorsal/anal fins that span nearly the full body length, and
iridescent turquoise/red/orange patterns. The "King of the Aquarium."
"""

import math
from PySide6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient,
    QLinearGradient, QPainterPath, QBrush
)
from PySide6.QtCore import QPointF, Qt
from engine.perlin import PerlinNoise


class DiscusSkin:
    """Photorealistic discus fish with vertical bars and iridescent patterns."""

    # Discus color morphs
    MORPHS = {
        "turquoise": {
            "base": [30, 160, 180],
            "bars": [20, 80, 100],
            "pattern": [60, 220, 240],
            "belly": [240, 160, 80],
        },
        "red_melon": {
            "base": [230, 100, 50],
            "bars": [180, 50, 30],
            "pattern": [255, 140, 70],
            "belly": [255, 200, 120],
        },
        "blue_diamond": {
            "base": [40, 80, 200],
            "bars": [25, 50, 140],
            "pattern": [80, 140, 255],
            "belly": [160, 180, 240],
        },
        "pigeon_blood": {
            "base": [240, 80, 60],
            "bars": [200, 40, 30],
            "pattern": [255, 120, 90],
            "belly": [255, 220, 180],
        },
        "leopard": {
            "base": [200, 160, 80],
            "bars": [120, 70, 30],
            "pattern": [240, 200, 120],
            "belly": [250, 230, 180],
        },
    }

    def __init__(self, seed=42, morph="turquoise"):
        self.perlin = PerlinNoise(seed=seed)
        self.perlin2 = PerlinNoise(seed=seed + 73)
        self.time = 0.0
        self.tail_phase = 0.0
        self.breath_phase = 0.0
        self.pectoral_phase = 0.0

        self.morph = morph
        colors = self.MORPHS.get(morph, self.MORPHS["turquoise"])
        self.base_col = colors["base"]
        self.bar_col = colors["bars"]
        self.pattern_col = colors["pattern"]
        self.belly_col = colors["belly"]

        self.size_scale = 1.0
        self.opacity = 0.93

        # Body flex
        self.body_flex = 0.0
        self._facing_left = False

    def set_colors(self, primary, secondary, accent):
        """Override base colors."""
        self.base_col = list(primary)
        self.pattern_col = list(secondary)
        self.bar_col = list(accent)

    def apply_config(self, config):
        fish_cfg = config.get("fish") if hasattr(config, "get") and callable(config.get) else {}
        if isinstance(fish_cfg, dict):
            # Keep discus readable even when global size is set very small.
            self.size_scale = max(0.85, fish_cfg.get("size_scale", self.size_scale))
            self.opacity = fish_cfg.get("opacity", self.opacity)

    def _c(self, rgb, alpha=255):
        """Make QColor with opacity."""
        return QColor(
            max(0, min(255, rgb[0])),
            max(0, min(255, rgb[1])),
            max(0, min(255, rgb[2])),
            max(0, min(255, int(alpha * self.opacity)))
        )

    def _lerp(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return [int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)]

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
        self.tail_phase += (0.07 + 0.05 * speed_factor) * (1.0 + speed_factor * 0.6)
        self.breath_phase += 0.03
        self.pectoral_phase += 0.12

        self.body_flex = math.sin(self.tail_phase * 0.4) * (2.0 + speed_factor * 3.0)

        sc = self.size_scale * 0.9  # Larger, more realistic discus presence
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

        self._draw_caudal_fin(painter, speed_factor)
        self._draw_anal_fin(painter, speed_factor)
        self._draw_body(painter)
        self._draw_vertical_bars(painter)
        self._draw_pattern_lines(painter)
        self._draw_dorsal_fin(painter, speed_factor)
        self._draw_pectoral_fin(painter, speed_factor)
        self._draw_eye(painter)
        self._draw_highlight(painter)

        painter.restore()

    def _draw_body(self, painter):
        """Large, round discus body - laterally compressed disc shape."""
        flex = self.body_flex

        body = QPainterPath()
        body.moveTo(28, 0)  # Mouth
        # Upper arc - very round
        body.cubicTo(
            24, -18 + flex * 0.3,
            8, -28 + flex * 0.5,
            -8, -26 + flex * 0.4
        )
        body.cubicTo(
            -20, -24 + flex * 0.2,
            -28, -16,
            -30, -4
        )
        # Peduncle
        body.cubicTo(-31, -2, -32, 0, -31, 2)
        body.cubicTo(-30, 4, -28, 8, -28, 16)
        # Lower arc
        body.cubicTo(
            -20, 24 - flex * 0.2,
            -8, 26 - flex * 0.4,
            8, 28 - flex * 0.5
        )
        body.cubicTo(
            24, 18 - flex * 0.3,
            28, 6,
            28, 0
        )

        # Rich gradient
        grad = QLinearGradient(0, -30, 0, 30)
        darker = self._lerp(self.base_col, [0, 0, 0], 0.2)
        lighter = self._lerp(self.base_col, [255, 255, 255], 0.15)
        grad.setColorAt(0.0, self._c(lighter, 220))
        grad.setColorAt(0.3, self._c(self.base_col, 235))
        grad.setColorAt(0.5, self._c(darker, 240))
        grad.setColorAt(0.7, self._c(self.base_col, 235))
        grad.setColorAt(1.0, self._c(self.belly_col, 210))

        outline = self._lerp(self.base_col, [0, 0, 0], 0.35)
        painter.setPen(QPen(self._c(outline, 100), 0.6))
        painter.setBrush(QBrush(grad))
        painter.drawPath(body)

    def _draw_vertical_bars(self, painter):
        """9 dark vertical bars characteristic of wild discus."""
        painter.setPen(Qt.NoPen)

        bar_positions = [-22, -16, -10, -4, 2, 8, 14, 20, 24]

        for i, bx in enumerate(bar_positions):
            # Bar intensity varies with Perlin noise
            intensity = 0.5 + 0.5 * self.perlin.noise2d(i * 0.5, self.time * 0.3)
            alpha = int(40 + intensity * 60)

            # Bar height follows body contour (wider in middle)
            t = (bx + 22) / 46.0  # normalize 0-1
            contour = math.sin(t * math.pi) ** 0.6
            half_height = 24 * contour

            bar = QPainterPath()
            bar.moveTo(bx - 1.5, -half_height)
            bar.cubicTo(bx - 1, -half_height * 0.5, bx - 0.5, 0, bx - 1, half_height * 0.5)
            bar.lineTo(bx - 1.5, half_height)
            bar.lineTo(bx + 1.5, half_height)
            bar.cubicTo(bx + 1, half_height * 0.5, bx + 0.5, 0, bx + 1, -half_height * 0.5)
            bar.lineTo(bx + 1.5, -half_height)
            bar.closeSubpath()

            painter.setBrush(self._c(self.bar_col, alpha))
            painter.drawPath(bar)

    def _draw_pattern_lines(self, painter):
        """Iridescent horizontal wavy lines (turquoise/metallic)."""
        painter.setPen(Qt.NoPen)

        num_lines = 8
        for i in range(num_lines):
            y_base = -18 + i * 5
            shimmer = self.perlin2.noise2d(i * 0.3, self.time * 0.6) * 0.3

            alpha = int(50 + 40 * (0.5 + shimmer))
            bright = self._lerp(self.pattern_col, [255, 255, 255], shimmer * 0.5)

            line = QPainterPath()
            # Wavy horizontal line following body contour
            points = []
            for j in range(12):
                t = j / 11.0
                lx = 22 - t * 48
                # Body contour width at this height
                body_t = abs(y_base) / 28.0
                if body_t > 0.95:
                    continue
                body_width = math.sqrt(max(0, 1 - body_t * body_t)) * 26
                if abs(lx) > body_width + 4:
                    continue
                noise = self.perlin.noise2d(lx * 0.1 + self.time * 0.5, y_base * 0.1) * 2
                points.append(QPointF(lx, y_base + noise))

            if len(points) < 3:
                continue

            line.moveTo(points[0])
            for p in points[1:]:
                line.lineTo(p)

            painter.setPen(QPen(self._c(bright, alpha), 1.2))
            painter.drawPath(line)

        painter.setPen(Qt.NoPen)

    def _draw_dorsal_fin(self, painter, speed_factor):
        """Long dorsal fin spanning most of the upper body."""
        num_pts = 18
        base_start = 20
        base_end = -26

        points = []
        for i in range(num_pts + 1):
            t = i / num_pts
            bx = base_start + (base_end - base_start) * t

            envelope = math.sin(t * math.pi) ** 0.5 * (1.0 - t * 0.15)
            height = 16 * envelope

            noise = self.perlin.octave_noise(t * 4.0, self.time * 0.9, octaves=2) * 4 * envelope
            wave = math.sin(self.tail_phase * 0.5 - t * 2.0) * (2 + 4 * speed_factor) * envelope

            # Body contour at this x position
            body_y = -24 * math.sin(((bx + 22) / 46.0) * math.pi) ** 0.6
            points.append(QPointF(bx, body_y - height + wave + noise))

        for layer, (la, ls) in enumerate([(90, 1.0), (40, 0.6)]):
            fin = QPainterPath()
            fin.moveTo(base_start, -18)
            for p in points:
                y = -18 + (p.y() - (-18)) * ls
                fin.lineTo(QPointF(p.x(), y))
            fin.lineTo(base_end, -22)
            # Close along body top
            fin.cubicTo(-20, -24, -8, -26, 8, -26)
            fin.cubicTo(16, -22, 20, -18, base_start, -18)

            grad = QLinearGradient(0, -42, 0, -18)
            edge_col = self._lerp(self.base_col, self.pattern_col, 0.5)
            grad.setColorAt(0.0, self._c(edge_col, int(la * 0.5)))
            grad.setColorAt(0.5, self._c(self.base_col, int(la * 0.8)))
            grad.setColorAt(1.0, self._c(self.base_col, la))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawPath(fin)

        # Rays
        painter.setPen(QPen(QColor(255, 255, 255, 18), 0.3))
        for i in range(1, num_pts, 2):
            t = i / num_pts
            bx = base_start + (base_end - base_start) * t
            painter.drawLine(QPointF(bx, -18 - 4 * math.sin(t * math.pi)), points[i])

    def _draw_anal_fin(self, painter, speed_factor):
        """Long anal fin along the bottom."""
        num_pts = 14
        base_start = 12
        base_end = -26

        points = []
        for i in range(num_pts + 1):
            t = i / num_pts
            bx = base_start + (base_end - base_start) * t

            envelope = math.sin(t * math.pi) ** 0.6
            depth = 14 * envelope

            noise = self.perlin.octave_noise(t * 3.5 + 15.0, self.time * 0.8, octaves=2) * 3 * envelope
            wave = math.sin(self.tail_phase * 0.6 - t * 2.2) * (2 + 4 * speed_factor) * envelope

            body_y = 24 * math.sin(((bx + 22) / 46.0) * math.pi) ** 0.6
            points.append(QPointF(bx, body_y + depth + wave + noise))

        for la, ls in [(80, 1.0), (35, 0.6)]:
            fin = QPainterPath()
            fin.moveTo(base_start, 18)
            for p in points:
                y = 18 + (p.y() - 18) * ls
                fin.lineTo(QPointF(p.x(), y))
            fin.lineTo(base_end, 22)
            fin.cubicTo(-20, 24, -8, 26, 8, 26)
            fin.cubicTo(12, 22, base_start, 18, base_start, 18)

            grad = QLinearGradient(0, 18, 0, 42)
            grad.setColorAt(0.0, self._c(self.base_col, la))
            grad.setColorAt(1.0, self._c(self._lerp(self.base_col, self.pattern_col, 0.4), int(la * 0.5)))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawPath(fin)

    def _draw_caudal_fin(self, painter, speed_factor):
        """Rounded caudal fin."""
        wave = math.sin(self.tail_phase) * (6 + 10 * speed_factor)
        noise = self.perlin.noise2d(self.time * 1.2, 5.0) * 4

        fin = QPainterPath()
        fin.moveTo(-30, -3)
        fin.cubicTo(-34, -10 + wave, -40, -14 + wave + noise, -42, -10 + wave)
        fin.cubicTo(-43, -5 + wave * 0.5, -43, 0, -43, 0)
        fin.cubicTo(-43, 0, -43, 5 + wave * 0.5, -42, 10 + wave)
        fin.cubicTo(-40, 14 + wave + noise, -34, 10 + wave, -30, 3)
        fin.closeSubpath()

        grad = QLinearGradient(-30, 0, -43, 0)
        grad.setColorAt(0.0, self._c(self.base_col, 160))
        grad.setColorAt(0.5, self._c(self._lerp(self.base_col, self.pattern_col, 0.3), 120))
        grad.setColorAt(1.0, self._c(self.pattern_col, 60))

        painter.setPen(QPen(self._c(self.bar_col, 30), 0.3))
        painter.setBrush(QBrush(grad))
        painter.drawPath(fin)

    def _draw_pectoral_fin(self, painter, speed_factor):
        """Small rounded pectoral fin."""
        flutter = math.sin(self.pectoral_phase) * 6

        fin = QPainterPath()
        fin.moveTo(14, 4)
        fin.cubicTo(18, 10 + flutter, 14, 16 + flutter, 6, 14 + flutter * 0.5)
        fin.cubicTo(4, 10 + flutter * 0.3, 8, 6, 14, 4)

        painter.setPen(QPen(self._c(self.base_col, 30), 0.3))
        painter.setBrush(self._c(self._lerp(self.base_col, [255, 255, 255], 0.2), 60))
        painter.drawPath(fin)

    def _draw_eye(self, painter):
        """Bright red-orange eye characteristic of discus."""
        ex, ey = 22, -4
        r = 4.5

        # Dark ring
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 10, 5, 160))
        painter.drawEllipse(QPointF(ex, ey), r + 1.0, r * 0.9 + 0.8)

        # Iris - bright red/orange (distinctive discus eye)
        iris_grad = QRadialGradient(ex - 0.3, ey - 0.3, r)
        iris_grad.setColorAt(0.0, QColor(220, 80, 30, 255))
        iris_grad.setColorAt(0.4, QColor(200, 60, 20, 255))
        iris_grad.setColorAt(0.8, QColor(160, 40, 15, 255))
        iris_grad.setColorAt(1.0, QColor(80, 20, 10, 255))

        painter.setBrush(QBrush(iris_grad))
        painter.drawEllipse(QPointF(ex, ey), r, r * 0.88)

        # Pupil
        painter.setBrush(QColor(2, 2, 2, 250))
        painter.drawEllipse(QPointF(ex, ey), r * 0.35, r * 0.33)

        # Highlight
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(QPointF(ex + 1.2, ey - 1.2), 1.0, 0.85)

        # Secondary highlight
        painter.setBrush(QColor(255, 255, 255, 100))
        painter.drawEllipse(QPointF(ex - 0.6, ey + 0.8), 0.5, 0.4)

    def _draw_highlight(self, painter):
        """Wet specular highlight on the round body."""
        h = QPainterPath()
        h.moveTo(20, -10)
        h.cubicTo(10, -18, -4, -20, -14, -16)
        h.cubicTo(-4, -15, 10, -12, 20, -10)

        painter.setPen(Qt.NoPen)
        grad = QLinearGradient(0, -22, 0, -10)
        grad.setColorAt(0.0, QColor(255, 255, 255, 40))
        grad.setColorAt(0.5, QColor(255, 255, 255, 22))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(grad))
        painter.drawPath(h)
