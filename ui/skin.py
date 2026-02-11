"""
Ultra-realistic Betta Fish renderer using QPainter.
Renders a photorealistic betta with:
  - Anatomically accurate teardrop body with muscle contour
  - Translucent, multi-layered halfmoon caudal fin (40+ segments)
  - Flowing dorsal with membrane + ray structure
  - Delicate trailing ventral fins with transparency gradient
  - Pectoral fins with independent flutter
  - Iridescent scales with light-angle shimmer
  - Realistic eye with corneal reflection
  - Body flex (S-curve) during swimming
  - Gill plate detail and mouth
"""

import math
import numpy as np
from PySide6.QtGui import (
    QPainter, QColor, QPolygonF, QPen, QRadialGradient,
    QLinearGradient, QPainterPath, QBrush, QConicalGradient
)
from PySide6.QtCore import QPointF, Qt
from engine.perlin import PerlinNoise


class FishSkin:
    """Photorealistic Betta fish with procedurally animated flowing fins."""


    FAMOUS_BETTA_PALETTES = {
        "nemo_galaxy": ([255, 118, 54], [35, 84, 170], [255, 240, 235]),
        "mustard_gas": ([26, 95, 195], [244, 190, 52], [255, 244, 184]),
        "koi_candy": ([240, 78, 62], [248, 244, 236], [35, 38, 42]),
        "black_orchid": ([34, 30, 56], [94, 70, 180], [210, 152, 255]),
        "copper_dragon": ([130, 82, 30], [212, 150, 67], [255, 229, 162]),
        "lavender_halfmoon": ([141, 95, 226], [230, 184, 255], [255, 238, 255]),
        "turquoise_butterfly": ([42, 176, 204], [18, 87, 154], [233, 247, 255]),
    }

    def __init__(self, config=None):
        self.perlin = PerlinNoise(seed=42)
        self.perlin2 = PerlinNoise(seed=137)  # Second noise for variety
        self.time = 0.0
        self.tail_phase = 0.0
        self.glow_phase = 0.0
        self.color_shift_phase = 0.0
        self.breath_phase = 0.0
        self.pectoral_phase = 0.0

        # Body flex for S-curve swimming
        self.body_flex = 0.0
        self.body_flex_target = 0.0

        # Default colors
        self.primary = [30, 80, 220]
        self.secondary = [180, 40, 120]
        self.accent = [255, 100, 200]
        self.color_shift_speed = 0.3
        self.enable_glow = True
        self.silhouette_strength = 1.0
        self.eye_tracking_strength = 0.75
        self.size_scale = 1.0
        self.opacity = 0.92
        self.tail_amp_factor = 1.0
        self.tail_freq_factor = 1.0
        self.turn_intensity = 0.0
        self.swim_cadence = 0.0
        self._facing_left = False

        if config:
            self.apply_config(config)

    def apply_config(self, config):
        fish_cfg = config.get("fish") if hasattr(config, "get") and callable(config.get) else {}
        if not fish_cfg:
            return
        if isinstance(fish_cfg, dict):
            palette_name = str(fish_cfg.get("betta_palette", "")).lower().strip()
            if palette_name in self.FAMOUS_BETTA_PALETTES:
                p, s2, a = self.FAMOUS_BETTA_PALETTES[palette_name]
                self.primary, self.secondary, self.accent = list(p), list(s2), list(a)

            self.primary = fish_cfg.get("primary_color", self.primary)
            self.secondary = fish_cfg.get("secondary_color", self.secondary)
            self.accent = fish_cfg.get("accent_color", self.accent)
            self.color_shift_speed = fish_cfg.get("color_shift_speed", self.color_shift_speed)
            self.enable_glow = fish_cfg.get("enable_glow", self.enable_glow)
            self.silhouette_strength = self._safe_clamped_float(
                fish_cfg.get("silhouette_strength", self.silhouette_strength),
                self.silhouette_strength,
                0.45,
                1.9,
            )
            self.eye_tracking_strength = self._safe_clamped_float(
                fish_cfg.get("eye_tracking_strength", self.eye_tracking_strength),
                self.eye_tracking_strength,
                0.0,
                1.0,
            )
            self.size_scale = fish_cfg.get("size_scale", self.size_scale)
            self.opacity = fish_cfg.get("opacity", self.opacity)

    def set_colors(self, primary, secondary, accent):
        self.primary = list(primary)
        self.secondary = list(secondary)
        self.accent = list(accent)

    @staticmethod
    def _safe_clamped_float(value, default, minimum, maximum):
        """Parse numeric config safely and clamp to allowed range."""
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return [int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)]

    def _shifted_color(self, base, phase_offset=0.0):
        t = (math.sin(self.color_shift_phase + phase_offset) + 1.0) / 2.0
        shifted = self._lerp_color(base, self.secondary, t * (0.25 + self.turn_intensity * 0.18 + self.swim_cadence * 0.08))
        return shifted

    def _make_color(self, rgb, alpha=255):
        return QColor(
            max(0, min(255, rgb[0])),
            max(0, min(255, rgb[1])),
            max(0, min(255, rgb[2])),
            max(0, min(255, int(alpha * self.opacity)))
        )

    def render(self, painter, local_pos, fish_state):
        x, y = local_pos
        vx, vy = fish_state["velocity"]
        speed = math.sqrt(vx * vx + vy * vy)

        if abs(vx) < 0.1 and abs(vy) < 0.1:
            angle = math.degrees(fish_state.get("facing_angle", 0))
        else:
            angle = math.degrees(math.atan2(vy, vx))

        hunger = fish_state.get("hunger", 0)
        mood = fish_state.get("mood", 100)
        state = fish_state.get("state", "IDLE")
        state_boost = 1.15 if state in {"DARTING", "FLARING"} else 1.0

        # Animation timing
        dt = 0.033
        speed_factor = min(speed / 120.0, 2.5)
        self.tail_amp_factor = fish_state.get("tail_amp_factor", 1.0)
        self.tail_freq_factor = fish_state.get("tail_freq_factor", 1.0)
        self.turn_intensity = fish_state.get("turn_intensity", 0.0)
        self.swim_cadence = fish_state.get("swim_cadence", speed_factor)
        self._state_boost = state_boost

        self.time += dt
        turn_boost = 1.0 + self.turn_intensity * 0.38
        self.tail_phase += ((0.08 + 0.06 * speed_factor) * (1.0 + speed_factor * 0.8)
                            * self.tail_freq_factor * turn_boost)
        self.glow_phase += 0.05
        self.color_shift_phase += self.color_shift_speed * dt
        self.breath_phase += 0.035
        self.pectoral_phase += 0.15 + speed_factor * 0.1

        # Body S-curve flex
        self.body_flex_target = math.sin(self.tail_phase * 0.4) * (3.0 + speed_factor * 5.0 + self.turn_intensity * 2.2) * (0.8 + self.tail_amp_factor * 0.35)
        self.body_flex += (self.body_flex_target - self.body_flex) * 0.12

        sc = self.size_scale
        # Hysteresis on left/right facing avoids flip jitter near +/-90°.
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

        # Render layers back to front
        self._draw_glow(painter, mood)
        self._draw_caudal_fin(painter, speed_factor)
        self._draw_anal_fin(painter, speed_factor)
        self._draw_ventral_fins(painter, speed_factor)
        self._draw_body(painter, hunger, mood, speed_factor)
        self._draw_dorsal_fin(painter, speed_factor)
        self._draw_pectoral_fins(painter, speed_factor)
        self._draw_gill_plate(painter)
        self._draw_eye(painter, mood, hunger, vx, vy)
        self._draw_scales(painter, speed_factor)
        self._draw_cheek_iridescence(painter)
        self._draw_body_highlight(painter)
        self._draw_silhouette_rim(painter, speed_factor)

        painter.restore()

    # ---- GLOW ----
    def _draw_glow(self, painter, mood):
        if not self.enable_glow:
            return
        glow_size = 62 + math.sin(self.glow_phase) * 9
        breath = math.sin(self.breath_phase) * 0.25 + 0.75
        glow_alpha = int(22 * breath * (mood / 100.0))
        col = self._shifted_color(self.primary, 0.5)

        gradient = QRadialGradient(0, 0, glow_size)
        gradient.setColorAt(0.0, self._make_color(col, glow_alpha))
        gradient.setColorAt(0.3, self._make_color(col, int(glow_alpha * 0.5)))
        gradient.setColorAt(0.7, self._make_color(col, int(glow_alpha * 0.15)))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(-5, 0), glow_size, glow_size * 0.6)

    # ---- BODY ----
    def _draw_body(self, painter, hunger, mood, speed_factor):
        col = self._shifted_color(self.primary)
        alpha = int(220 + (mood / 100.0) * 35)
        flex = self.body_flex

        body_path = QPainterPath()
        # Anatomically accurate teardrop: pointed mouth, wide mid-body, tapered peduncle
        body_path.moveTo(32, 0)  # Mouth tip
        # Upper contour
        body_path.cubicTo(
            29, -5 + flex * 0.3,
            17, -16 + flex * 0.5,
            0, -17 + flex * 0.72
        )
        body_path.cubicTo(
            -13, -17 + flex * 0.62,
            -25, -12 + flex * 0.3,
            -31, -5 + flex * 0.1
        )
        # Caudal peduncle (narrow tail base)
        body_path.cubicTo(-34, -3, -37, -2, -38, 0)
        # Lower contour
        body_path.cubicTo(-37, 2, -34, 3, -31, 5 - flex * 0.1)
        body_path.cubicTo(
            -25, 12 - flex * 0.3,
            -13, 17 - flex * 0.62,
            0, 17 - flex * 0.72
        )
        body_path.cubicTo(
            17, 16 - flex * 0.5,
            29, 5 - flex * 0.3,
            32, 0
        )

        # Multi-stop gradient for realistic shading
        body_grad = QLinearGradient(0, -18, 0, 18)
        lighter = self._lerp_color(col, [255, 255, 255], 0.2)
        darker = self._lerp_color(col, [0, 0, 20], 0.3)
        belly = self._lerp_color(col, [255, 255, 255], 0.35)
        body_grad.setColorAt(0.0, self._make_color(lighter, alpha))
        body_grad.setColorAt(0.25, self._make_color(col, alpha))
        body_grad.setColorAt(0.5, self._make_color(darker, alpha))
        body_grad.setColorAt(0.75, self._make_color(col, alpha))
        body_grad.setColorAt(1.0, self._make_color(belly, int(alpha * 0.95)))

        # Subtle dark outline
        outline_col = self._lerp_color(col, [0, 0, 0], 0.4)
        painter.setPen(QPen(self._make_color(outline_col, 100), 0.7))
        painter.setBrush(QBrush(body_grad))
        painter.drawPath(body_path)

        # Lateral line (subtle dark line along midline)
        painter.setPen(QPen(self._make_color(self._lerp_color(col, [0, 0, 0], 0.2), 40), 0.5))
        lat_path = QPainterPath()
        lat_path.moveTo(24, 0)
        lat_path.cubicTo(12, -1 + flex * 0.2, -10, 0 + flex * 0.3, -30, 0)
        painter.drawPath(lat_path)

    def _draw_body_highlight(self, painter):
        """Wet specular highlight along the body."""
        highlight = QPainterPath()
        highlight.moveTo(26, -5)
        highlight.cubicTo(18, -10, 4, -11, -8, -9)
        highlight.cubicTo(4, -8, 18, -7, 26, -5)

        painter.setPen(Qt.NoPen)
        h_grad = QLinearGradient(10, -12, 10, -5)
        h_grad.setColorAt(0.0, QColor(255, 255, 255, 45))
        h_grad.setColorAt(0.5, QColor(255, 255, 255, 25))
        h_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(h_grad))
        painter.drawPath(highlight)

    def _draw_cheek_iridescence(self, painter):
        """Subtle gill-cheek iridescence patch for real betta face depth."""
        grad = QRadialGradient(15.5, -2.5, 8.0)
        grad.setColorAt(0.0, self._make_color(self._lerp_color(self.accent, [220, 255, 255], 0.45), 58))
        grad.setColorAt(0.55, self._make_color(self._lerp_color(self.primary, self.accent, 0.35), 32))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(15.2, -2.0), 7.4, 5.6)

        # Subtle maxilla highlight near mouth for stronger head read.
        jaw_grad = QRadialGradient(27.5, 0.0, 4.8)
        jaw_grad.setColorAt(0.0, self._make_color([250, 240, 232], 30))
        jaw_grad.setColorAt(0.7, self._make_color(self._lerp_color(self.primary, [30, 20, 20], 0.45), 18))
        jaw_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(jaw_grad))
        painter.drawEllipse(QPointF(27.2, -0.2), 4.2, 2.8)

    # ---- CAUDAL (TAIL) FIN ----
    def _draw_silhouette_rim(self, painter, speed_factor):
        """Crisp rim light to improve Uno outline readability on mixed desktops."""
        rim = QPainterPath()
        flex = self.body_flex
        rim.moveTo(31.5, -0.3)
        rim.cubicTo(27.0, -7 + flex * 0.2, 10, -14 + flex * 0.3, -24, -11 + flex * 0.2)
        rim.cubicTo(-31, -6 + flex * 0.1, -37, -2, -38, 0)
        rim.cubicTo(-37, 2, -31, 6 - flex * 0.1, -24, 11 - flex * 0.2)
        rim.cubicTo(10, 14 - flex * 0.3, 27, 7 - flex * 0.2, 31.5, 0.3)

        rim_alpha = int((32 + 16 * min(1.0, speed_factor * 0.55 + self.turn_intensity * 0.6)) * self.silhouette_strength)
        rim_col = self._lerp_color(self.accent, [255, 255, 255], 0.45)
        painter.setPen(QPen(self._make_color(rim_col, rim_alpha), 0.9))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(rim)

    def _draw_caudal_fin(self, painter, speed_factor):
        """Massive halfmoon caudal fin with translucent membrane and ray structure."""
        num_rays = 32
        fin_length = 68 + self.swim_cadence * 3.0
        fin_spread = 58 + self.turn_intensity * 4.0  # Halfmoon = wide spread

        col_top = self._shifted_color(self.accent, 1.0)
        col_mid = self._shifted_color(self.primary, 1.5)
        col_bot = self._shifted_color(self.secondary, 2.0)

        # Generate upper and lower edges with organic waviness
        upper_points = [QPointF(-28, -4)]
        lower_points = [QPointF(-28, 4)]
        center_points = [QPointF(-28, 0)]

        for i in range(1, num_rays + 1):
            t = i / num_rays
            px = -28 - t * fin_length

            # Multi-octave noise for realistic membrane ripple
            noise_u = self.perlin.octave_noise(t * 4.0, self.time * 1.2, octaves=3) * 14 * t
            noise_l = self.perlin.octave_noise(t * 4.0 + 10.0, self.time * 1.2, octaves=3) * 14 * t
            noise_c = self.perlin2.noise2d(t * 3.0, self.time * 1.0) * 8 * t

            # Primary wave: large sweeping motion
            wave = math.sin(self.tail_phase - t * 2.8) * (8 + t * 24) * (0.5 + speed_factor * 0.52) * self.tail_amp_factor * self._state_boost
            # Secondary wave: smaller, faster
            wave2 = math.sin(self.tail_phase * 1.7 - t * 4.0) * (3 + t * 8)

            spread = t * fin_spread
            # Halfmoon shape: spread increases then slightly curves back
            spread_curve = spread * (1.0 + 0.15 * math.sin(t * math.pi))

            upper_points.append(QPointF(px, -spread_curve + wave + wave2 + noise_u))
            lower_points.append(QPointF(px, spread_curve + wave + wave2 + noise_l))
            center_points.append(QPointF(px, wave + noise_c))

        # Draw multiple translucent membrane layers for depth
        for layer in range(3):
            layer_alpha = [90, 60, 35][layer]
            layer_scale = [1.0, 0.85, 0.65][layer]
            layer_offset = [0, 2, 5][layer]

            fin_path = QPainterPath()
            fin_path.moveTo(upper_points[0])

            for i in range(1, len(upper_points)):
                p = upper_points[i]
                scaled_y = p.y() * layer_scale - layer_offset
                fin_path.lineTo(QPointF(p.x(), scaled_y))

            for i in range(len(lower_points) - 1, -1, -1):
                p = lower_points[i]
                scaled_y = p.y() * layer_scale + layer_offset
                fin_path.lineTo(QPointF(p.x(), scaled_y))
            fin_path.closeSubpath()

            # Gradient across the fin
            fin_grad = QLinearGradient(-28, -fin_spread, -28, fin_spread)
            fin_grad.setColorAt(0.0, self._make_color(col_top, layer_alpha))
            fin_grad.setColorAt(0.3, self._make_color(col_mid, int(layer_alpha * 0.85)))
            fin_grad.setColorAt(0.5, self._make_color(
                self._lerp_color(col_mid, [255, 255, 255], 0.15), int(layer_alpha * 0.7)))
            fin_grad.setColorAt(0.7, self._make_color(col_mid, int(layer_alpha * 0.85)))
            fin_grad.setColorAt(1.0, self._make_color(col_bot, layer_alpha))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fin_grad))
            painter.drawPath(fin_path)

        # Fin ray lines (branching structure)
        for i in range(2, num_rays, 2):
            t = i / num_rays
            # Ray opacity fades toward edges
            ray_alpha = int(35 * (1.0 - t * 0.5))
            ray_col = self._lerp_color(self.primary, [255, 255, 255], 0.3)
            painter.setPen(QPen(self._make_color(ray_col, ray_alpha), 0.4))

            # Upper ray
            painter.drawLine(upper_points[0], upper_points[i])
            # Center ray
            painter.drawLine(center_points[0], center_points[i])
            # Lower ray
            painter.drawLine(lower_points[0], lower_points[i])

        # Delicate edge highlight
        painter.setPen(QPen(self._make_color([255, 255, 255], 20), 0.6))
        edge_path = QPainterPath()
        edge_path.moveTo(upper_points[0])
        for p in upper_points[1:]:
            edge_path.lineTo(p)
        painter.drawPath(edge_path)

        edge_path2 = QPainterPath()
        edge_path2.moveTo(lower_points[0])
        for p in lower_points[1:]:
            edge_path2.lineTo(p)
        painter.drawPath(edge_path2)

        # Trailing filament tips for premium halfmoon silhouette.
        painter.setPen(QPen(self._make_color(self._lerp_color(col_top, [255, 255, 255], 0.5), 20), 0.55))
        for idx in range(max(4, num_rays - 7), num_rays + 1, 2):
            p_up = upper_points[idx]
            p_lo = lower_points[idx]
            painter.drawLine(p_up, QPointF(p_up.x() - 4.0, p_up.y() - 2.0))
            painter.drawLine(p_lo, QPointF(p_lo.x() - 4.0, p_lo.y() + 2.0))

    # ---- DORSAL FIN ----
    def _draw_dorsal_fin(self, painter, speed_factor):
        """Tall flowing dorsal fin with membrane transparency and ray branching."""
        num_pts = 20
        col = self._shifted_color(self.accent, 0.8)

        base_start_x = 18
        base_end_x = -26

        points = []
        for i in range(num_pts + 1):
            t = i / num_pts
            bx = base_start_x + (base_end_x - base_start_x) * t

            # Taller peak envelope, asymmetric (higher toward front)
            envelope = math.sin(t * math.pi) ** 0.6 * (1.0 - t * 0.2)
            base_height = (40 + self.swim_cadence * 4.0) * envelope

            noise = self.perlin.octave_noise(t * 5.0 + 5.0, self.time * 1.0, octaves=3) * 6 * envelope
            wave = math.sin(self.tail_phase * 0.6 - t * 2.5) * (3 + 7.6 * speed_factor) * envelope * (0.9 + self.tail_amp_factor * 0.28) * self._state_boost
            wave2 = math.sin(self.tail_phase * 1.3 - t * 3.5) * 2 * envelope

            points.append(QPointF(bx, -13 - base_height + wave + wave2 + noise))

        # Two layers for translucency effect
        for layer, (l_alpha, l_scale) in enumerate([(110, 1.0), (55, 0.7)]):
            fin_path = QPainterPath()
            fin_path.moveTo(base_start_x, -11)
            for p in points:
                y = -11 + (p.y() - (-11)) * l_scale
                fin_path.lineTo(QPointF(p.x(), y))
            fin_path.lineTo(base_end_x, -11)
            fin_path.closeSubpath()

            fin_grad = QLinearGradient(0, -52, 0, -11)
            fin_grad.setColorAt(0.0, self._make_color(col, int(l_alpha * 0.5)))
            fin_grad.setColorAt(0.4, self._make_color(
                self._lerp_color(col, self.primary, 0.4), int(l_alpha * 0.8)))
            fin_grad.setColorAt(1.0, self._make_color(self.primary, l_alpha))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fin_grad))
            painter.drawPath(fin_path)

        # Fin rays with branching
        painter.setPen(QPen(self._make_color([255, 255, 255], 20), 0.35))
        for i in range(1, num_pts, 2):
            t = i / num_pts
            bx = base_start_x + (base_end_x - base_start_x) * t
            painter.drawLine(QPointF(bx, -11), points[i])
            # Branch at 60% height
            if i + 1 <= num_pts:
                mid_x = bx + (points[i].x() - bx) * 0.6
                mid_y = -11 + (points[i].y() - (-11)) * 0.6
                painter.drawLine(QPointF(mid_x, mid_y), QPointF(mid_x + 3, mid_y - 4))

        # Edge highlight
        painter.setPen(QPen(self._make_color(self._lerp_color(col, [255, 255, 255], 0.3), 25), 0.5))
        edge = QPainterPath()
        edge.moveTo(points[0])
        for p in points[1:]:
            edge.lineTo(p)
        painter.drawPath(edge)

    # ---- ANAL FIN ----
    def _draw_anal_fin(self, painter, speed_factor):
        """Flowing anal fin with translucent membrane."""
        num_pts = 16
        col = self._shifted_color(self.secondary, 1.5)

        base_start_x = 8
        base_end_x = -28

        points = []
        for i in range(num_pts + 1):
            t = i / num_pts
            bx = base_start_x + (base_end_x - base_start_x) * t

            envelope = math.sin(t * math.pi) ** 0.7
            base_depth = (30 + self.swim_cadence * 2.6) * envelope

            noise = self.perlin.octave_noise(t * 4.0 + 20.0, self.time * 1.1, octaves=3) * 5 * envelope
            wave = math.sin(self.tail_phase * 0.7 - t * 2.4) * (3 + 6.8 * speed_factor) * envelope * (0.9 + self.tail_amp_factor * 0.24) * self._state_boost

            points.append(QPointF(bx, 12 + base_depth + wave + noise))

        for layer, (l_alpha, l_scale) in enumerate([(100, 1.0), (45, 0.65)]):
            fin_path = QPainterPath()
            fin_path.moveTo(base_start_x, 10)
            for p in points:
                y = 10 + (p.y() - 10) * l_scale
                fin_path.lineTo(QPointF(p.x(), y))
            fin_path.lineTo(base_end_x, 10)
            fin_path.closeSubpath()

            fin_grad = QLinearGradient(0, 10, 0, 42)
            fin_grad.setColorAt(0.0, self._make_color(self.primary, l_alpha))
            fin_grad.setColorAt(0.5, self._make_color(
                self._lerp_color(col, self.primary, 0.3), int(l_alpha * 0.8)))
            fin_grad.setColorAt(1.0, self._make_color(col, int(l_alpha * 0.5)))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fin_grad))
            painter.drawPath(fin_path)

        # Rays
        painter.setPen(QPen(self._make_color([255, 255, 255], 16), 0.3))
        for i in range(1, num_pts, 2):
            t = i / num_pts
            bx = base_start_x + (base_end_x - base_start_x) * t
            painter.drawLine(QPointF(bx, 10), points[i])

    # ---- VENTRAL FINS ----
    def _draw_ventral_fins(self, painter, speed_factor):
        """Long, elegant trailing ventral fins with transparency gradient."""
        col = self._shifted_color(self.accent, 2.5)

        for side in [-1, 1]:
            num_pts = 18
            points = [QPointF(8, side * 9)]

            for i in range(1, num_pts + 1):
                t = i / num_pts

                noise = self.perlin.octave_noise(
                    t * 3.5 + side * 30.0, self.time * 0.8 + side * 5.0, octaves=3
                ) * 8 * t
                wave = math.sin(self.tail_phase * 0.5 - t * 1.6 + side * 0.4) * (4 + 10 * speed_factor) * t * (0.9 + self.tail_amp_factor * 0.2)

                px = 8 - t * 40
                py = side * (9 + t * 42) + wave + noise

                points.append(QPointF(px, py))

            # Multiple transparency layers
            for layer in range(2):
                l_alpha = [75, 35][layer]
                l_width = [1.0, 0.6][layer]

                fin_path = QPainterPath()
                fin_path.moveTo(points[0])
                for i in range(1, len(points) - 1, 2):
                    ctrl = points[i]
                    end = points[min(i + 1, len(points) - 1)]
                    # Scale width
                    ctrl_y = points[0].y() + (ctrl.y() - points[0].y()) * l_width
                    end_y = points[0].y() + (end.y() - points[0].y()) * l_width
                    fin_path.quadTo(QPointF(ctrl.x(), ctrl_y), QPointF(end.x(), end_y))
                if len(points) % 2 == 0:
                    p = points[-1]
                    fin_path.lineTo(QPointF(p.x(), points[0].y() + (p.y() - points[0].y()) * l_width))

                fin_path.lineTo(QPointF(10, side * 7))
                fin_path.closeSubpath()

                # Gradient fading toward tips
                fy_start = side * 9
                fy_end = side * 50
                fin_grad = QLinearGradient(0, fy_start, 0, fy_end)
                fin_grad.setColorAt(0.0, self._make_color(self.primary, l_alpha))
                fin_grad.setColorAt(0.3, self._make_color(col, int(l_alpha * 0.9)))
                fin_grad.setColorAt(0.7, self._make_color(col, int(l_alpha * 0.5)))
                fin_grad.setColorAt(1.0, self._make_color(col, int(l_alpha * 0.15)))

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(fin_grad))
                painter.drawPath(fin_path)

            # Delicate ray lines
            painter.setPen(QPen(self._make_color([255, 255, 255], 12), 0.25))
            for i in range(2, len(points), 3):
                painter.drawLine(points[0], points[i])

    # ---- PECTORAL FINS ----
    def _draw_pectoral_fins(self, painter, speed_factor):
        """Small pectoral fins with independent flutter rhythm."""
        col = self._shifted_color(self.primary, 3.0)

        # Flutter motion
        flutter = math.sin(self.pectoral_phase) * (8 + self.turn_intensity * 2.0)
        flutter2 = math.sin(self.pectoral_phase * 0.7 + 1.0) * (5 + self.turn_intensity * 1.5)

        for side_mult in [1]:  # Only visible side (the other is hidden by body)
            fin_path = QPainterPath()
            fin_path.moveTo(12, 3 * side_mult)
            fin_path.cubicTo(
                QPointF(20, (10 + flutter) * side_mult),
                QPointF(16, (18 + flutter2) * side_mult),
                QPointF(6, (15 + flutter * 0.5) * side_mult)
            )
            fin_path.cubicTo(
                QPointF(4, (10 + flutter * 0.3) * side_mult),
                QPointF(8, (5) * side_mult),
                QPointF(12, 3 * side_mult)
            )

            fin_grad = QRadialGradient(12, 10 * side_mult, 16)
            fin_grad.setColorAt(0.0, self._make_color(col, 80))
            fin_grad.setColorAt(0.5, self._make_color(col, 50))
            fin_grad.setColorAt(1.0, self._make_color(col, 15))

            painter.setPen(QPen(self._make_color(col, 30), 0.3))
            painter.setBrush(QBrush(fin_grad))
            painter.drawPath(fin_path)

    # ---- GILL PLATE ----
    def _draw_gill_plate(self, painter):
        """Gill plate, operculum shading, and expressive mouth geometry."""
        col = self._lerp_color(self.primary, [0, 0, 0], 0.15)

        # Operculum volume shadow gives head mass near gill cover.
        operculum = QRadialGradient(14.0, 0.0, 11.0)
        operculum.setColorAt(0.0, self._make_color(self._lerp_color(self.primary, [18, 16, 24], 0.38), 44))
        operculum.setColorAt(0.6, self._make_color(self._lerp_color(self.primary, [18, 16, 24], 0.54), 26))
        operculum.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(operculum))
        painter.drawEllipse(QPointF(14.0, 0.0), 10.5, 9.0)

        breath = math.sin(self.breath_phase * 2.0) * 1.6
        painter.setBrush(Qt.NoBrush)

        # Primary gill arc (main plate seam).
        painter.setPen(QPen(self._make_color(col, 58), 0.9))
        gill_path = QPainterPath()
        gill_path.moveTo(16.8, -9.0)
        gill_path.cubicTo(14.4, -4.5, 14.1, 4.6 + breath, 16.7, 9.0)
        painter.drawPath(gill_path)

        # Secondary inner seam.
        gill_path2 = QPainterPath()
        gill_path2.moveTo(14.5, -7.0)
        gill_path2.cubicTo(12.6, -3.3, 12.4, 3.6 + breath * 0.7, 14.4, 7.0)
        painter.setPen(QPen(self._make_color(col, 34), 0.55))
        painter.drawPath(gill_path2)

        # Mouth line with slight pout/extension at inhale.
        mouth_open = max(0.0, math.sin(self.breath_phase * 1.5) * 1.0)
        pout = 0.7 + mouth_open * 0.45
        lip_col = self._lerp_color(self.primary, [0, 0, 0], 0.34)
        painter.setPen(QPen(self._make_color(lip_col, 78), 0.72))

        mouth_upper = QPainterPath()
        mouth_upper.moveTo(32.0, -0.1)
        mouth_upper.cubicTo(31.0, -1.8, 30.0 + pout * 0.1, -2.1 - mouth_open, 28.6 + pout, -0.55)
        painter.drawPath(mouth_upper)

        mouth_lower = QPainterPath()
        mouth_lower.moveTo(32.0, 0.1)
        mouth_lower.cubicTo(31.0, 1.9, 30.0 + pout * 0.1, 2.1 + mouth_open, 28.6 + pout, 0.58)
        painter.drawPath(mouth_lower)

        # Tiny reflective lip highlight.
        painter.setPen(QPen(self._make_color([255, 242, 232], 34), 0.35))
        painter.drawLine(QPointF(30.2, -0.7), QPointF(28.9 + pout * 0.25, -0.34))

    # ---- EYE ----
    def _draw_eye(self, painter, mood, hunger, vx=0.0, vy=0.0):
        """Photorealistic eye with corneal reflection and depth."""
        eye_x, eye_y = 22.6, -4.1
        eye_r = 5.15

        speed = math.sqrt(vx * vx + vy * vy)
        look_scale = self.eye_tracking_strength * min(1.0, speed / 180.0)
        look_x = max(-0.9, min(0.9, (vx / max(1.0, speed)) * 0.85 * look_scale))
        look_y = max(-0.55, min(0.55, (vy / max(1.0, speed)) * 0.55 * look_scale))
        iris_x = eye_x + look_x
        iris_y = eye_y + look_y

        # Dorsal eyelid shadow for depth/readability.
        lid_grad = QRadialGradient(eye_x - 0.6, eye_y - 1.6, eye_r * 1.1)
        lid_grad.setColorAt(0.0, self._make_color(self._lerp_color(self.primary, [16, 14, 18], 0.45), 44))
        lid_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(lid_grad))
        painter.drawEllipse(QPointF(eye_x - 0.3, eye_y - 1.1), eye_r * 1.0, eye_r * 0.72)

        # Dark ring around eye
        ring_col = self._lerp_color(self.primary, [0, 0, 0], 0.5)
        painter.setBrush(self._make_color(ring_col, 120))
        painter.drawEllipse(QPointF(eye_x, eye_y), eye_r + 1.2, eye_r * 0.95 + 1.0)

        # Sclera with slight warm tint
        painter.setPen(QPen(QColor(60, 55, 50, 180), 0.5))
        sclera_grad = QRadialGradient(eye_x, eye_y, eye_r)
        sclera_grad.setColorAt(0.0, QColor(248, 245, 242, 240))
        sclera_grad.setColorAt(0.7, QColor(235, 228, 220, 235))
        sclera_grad.setColorAt(1.0, QColor(200, 190, 180, 220))
        painter.setBrush(QBrush(sclera_grad))
        painter.drawEllipse(QPointF(eye_x, eye_y), eye_r, eye_r * 0.88)

        # Iris - deep complex coloring
        stress = min(1.0, 0.65 * (hunger / 100.0) + 0.35 * (1.0 - mood / 100.0))
        iris_calm = [20, 35, 90]
        iris_stressed = [170, 55, 25]
        iris_col = self._lerp_color(iris_calm, iris_stressed, stress)

        iris_r = eye_r * 0.72
        iris_grad = QRadialGradient(iris_x - 0.3, iris_y - 0.3, iris_r)
        iris_grad.setColorAt(0.0, QColor(
            min(255, iris_col[0] + 40),
            min(255, iris_col[1] + 30),
            min(255, iris_col[2] + 20), 255))
        iris_grad.setColorAt(0.3, QColor(iris_col[0], iris_col[1], iris_col[2], 255))
        iris_grad.setColorAt(0.7, QColor(
            max(0, iris_col[0] - 30),
            max(0, iris_col[1] - 25),
            max(0, iris_col[2] - 15), 255))
        iris_grad.setColorAt(1.0, QColor(25, 20, 15, 255))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(iris_grad))
        painter.drawEllipse(QPointF(iris_x, iris_y), iris_r, iris_r * 0.95)

        # Iris texture (radial lines)
        painter.setPen(QPen(QColor(
            min(255, iris_col[0] + 60),
            min(255, iris_col[1] + 40),
            min(255, iris_col[2] + 30), 30), 0.2))
        for angle in range(0, 360, 20):
            rad = math.radians(angle)
            inner_r = iris_r * 0.3
            outer_r = iris_r * 0.9
            painter.drawLine(
                QPointF(iris_x + math.cos(rad) * inner_r, iris_y + math.sin(rad) * inner_r * 0.95),
                QPointF(iris_x + math.cos(rad) * outer_r, iris_y + math.sin(rad) * outer_r * 0.95)
            )

        # Pupil with depth
        pupil_size = eye_r * (0.3 + 0.1 * (1.0 - mood / 100.0))
        pupil_grad = QRadialGradient(iris_x, iris_y, pupil_size)
        pupil_grad.setColorAt(0.0, QColor(2, 2, 2, 250))
        pupil_grad.setColorAt(0.7, QColor(8, 5, 3, 245))
        pupil_grad.setColorAt(1.0, QColor(15, 10, 8, 235))
        painter.setBrush(QBrush(pupil_grad))
        painter.drawEllipse(QPointF(iris_x, iris_y), pupil_size, pupil_size * 0.92)

        # Primary specular highlight (corneal reflection)
        painter.setBrush(QColor(255, 255, 255, 215))
        painter.drawEllipse(QPointF(iris_x + 1.55, iris_y - 1.55), 1.35, 1.15)

        # Secondary smaller highlight
        painter.setBrush(QColor(255, 255, 255, 128))
        painter.drawEllipse(QPointF(iris_x - 0.75, iris_y + 0.95), 0.68, 0.56)

        # Tiny glint for wet-eye realism.
        painter.setBrush(QColor(255, 255, 255, 86))
        painter.drawEllipse(QPointF(iris_x + 0.25, iris_y - 0.05), 0.32, 0.28)

    # ---- SCALES ----
    def _draw_scales(self, painter, speed_factor):
        """Iridescent scale pattern that shimmers with angle."""
        shimmer_base = 12 + 8 * math.sin(self.time * 1.5) + self.swim_cadence * 6 + self.turn_intensity * 5
        painter.setPen(Qt.NoPen)

        # Scale rows following body contour
        scale_rows = [
            (-7, 5, 7),   # (y_offset, num_cols, start_x)
            (0, 8, 10),
            (7, 7, 8),
        ]

        for y_off, num_cols, start_x in scale_rows:
            for col_idx in range(num_cols):
                t = col_idx / max(1, num_cols - 1)
                sx = start_x - col_idx * 6.5
                sy = y_off

                # Shimmer based on position and time
                shimmer = self.perlin.noise2d(
                    sx * 0.1 + self.time * 0.8,
                    sy * 0.1 + self.time * 0.3
                )
                alpha = max(0, min(60, int(shimmer_base + shimmer * 25)))

                # Iridescent color shift per scale
                irid_shift = self.perlin2.noise2d(sx * 0.05, sy * 0.05 + self.time * 0.5)
                if irid_shift > 0.2:
                    scale_col = self._lerp_color(self.primary, [200, 255, 255], irid_shift * 0.5)
                elif irid_shift < -0.2:
                    scale_col = self._lerp_color(self.primary, [255, 200, 255], abs(irid_shift) * 0.5)
                else:
                    scale_col = self._lerp_color([255, 255, 255], self.primary, 0.3)

                painter.setBrush(self._make_color(scale_col, alpha))
                # Crescent-shaped scales
                scale_path = QPainterPath()
                scale_path.moveTo(sx - 2.5, sy)
                scale_path.cubicTo(
                    sx - 1.5, sy - 2.8,
                    sx + 1.5, sy - 2.8,
                    sx + 2.5, sy
                )
                scale_path.cubicTo(
                    sx + 1.2, sy - 1.0,
                    sx - 1.2, sy - 1.0,
                    sx - 2.5, sy
                )
                painter.drawPath(scale_path)
