"""
Ethereal Cyan Jellyfish - Bioluminescent Deep Sea Moon Jelly
Matches the reference image: glowing cyan/turquoise translucent jellyfish
with soft dome bell, long flowing tentacles, and ambient light particles.

Features:
- Soft translucent dome bell with bright cyan core glow
- Smooth pulsing propulsion animation
- Long flowing tentacles with sinusoidal sway
- Ambient bioluminescent particles drifting around
- Radial glow halo emanating from the bell
- Ethereal, dreamy deep-sea aesthetic
"""

import math
import random
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QRadialGradient,
    QLinearGradient, QBrush, QPen
)
from PySide6.QtCore import QPointF, Qt


class CyanJellyfishSkin:
    """
    Ethereal cyan bioluminescent jellyfish.
    Soft glowing moon-jelly aesthetic with ambient particles.
    """

    # Cyan / turquoise palette
    GLOW_CORE = QColor(180, 255, 255, 220)       # Bright white-cyan core
    GLOW_MID = QColor(0, 240, 255, 160)           # Vivid cyan
    GLOW_OUTER = QColor(0, 180, 220, 80)          # Softer turquoise
    BELL_FILL = QColor(20, 200, 230, 100)         # Translucent cyan bell
    BELL_EDGE = QColor(60, 230, 255, 140)         # Brighter bell rim
    TENTACLE_BASE = QColor(0, 200, 240, 120)      # Tentacle root
    TENTACLE_TIP = QColor(0, 160, 200, 30)        # Fading tentacle tip
    PARTICLE_COLOR = QColor(140, 240, 255, 180)   # Ambient particles

    def __init__(self, config=None):
        self.time = 0.0
        self.pulse_phase = 0.0
        self.glow_intensity = 0.6
        self.flash_triggered = False
        self.flash_timer = 0.0

        # Bell animation
        self.bell_contraction = 0.0
        self.bell_radius = 40
        self.bell_height = 35

        # Tentacles
        self.num_tentacles = 14
        self.tentacle_lengths = [
            random.uniform(90, 160) for _ in range(self.num_tentacles)
        ]
        self.tentacle_phases = [
            random.uniform(0, math.pi * 2) for _ in range(self.num_tentacles)
        ]
        self.tentacle_speeds = [
            random.uniform(0.02, 0.05) for _ in range(self.num_tentacles)
        ]

        # Oral arms (shorter, thicker inner appendages)
        self.num_oral_arms = 4
        self.oral_arm_phases = [
            random.uniform(0, math.pi * 2) for _ in range(self.num_oral_arms)
        ]

        # Ambient particles
        self.particles = []
        for _ in range(35):
            self.particles.append(self._new_particle())

        # Scale / state
        self.size_scale = 1.0
        self.opacity = 0.95
        self._facing_left = False

        if config:
            self.apply_config(config)

    def apply_config(self, config):
        fish_cfg = config.get("fish") if hasattr(config, "get") else {}
        if isinstance(fish_cfg, dict):
            self.size_scale = fish_cfg.get("size_scale", self.size_scale)

    def _new_particle(self, near_origin=False):
        """Create a new ambient particle."""
        if near_origin:
            px = random.uniform(-120, 120)
            py = random.uniform(-80, 180)
        else:
            px = random.uniform(-200, 200)
            py = random.uniform(-150, 250)
        return {
            "x": px,
            "y": py,
            "vx": random.uniform(-8, 8),
            "vy": random.uniform(-15, -3),
            "size": random.uniform(1.0, 3.5),
            "life": random.uniform(0.6, 1.0),
            "phase": random.uniform(0, math.pi * 2),
            "pulse_speed": random.uniform(1.5, 4.0),
        }

    def trigger_flash(self):
        """Trigger a bright bioluminescent flash."""
        self.flash_triggered = True
        self.flash_timer = 0.0
        self.glow_intensity = 1.0

    def render(self, painter, local_pos, fish_state):
        """Main render entry point (sector-based rendering)."""
        x = fish_state.get("position", [0, 0])[0]
        y = fish_state.get("position", [0, 0])[1]
        angle = fish_state.get("facing_angle", 0)
        self.update_and_render(painter, x, y, angle, fish_state)

    def update_and_render(self, painter, x, y, angle, fish_state):
        """Update animation state and render the jellyfish.

        Jellyfish stays UPRIGHT - tentacles always hang down.
        """
        vx = fish_state.get("velocity", [0, 0])[0]
        vy = fish_state.get("velocity", [0, 0])[1]
        speed = math.hypot(vx, vy)

        dt = 0.033
        self.time += dt

        # Bell pulsing
        speed_factor = min(speed / 100.0, 2.0)
        pulse_speed = 0.06 + speed_factor * 0.03
        self.pulse_phase += pulse_speed
        self.bell_contraction = (math.sin(self.pulse_phase) + 1) / 2

        # Flash decay
        if self.flash_triggered:
            self.flash_timer += dt * 5
            self.glow_intensity = max(0.4, 1.0 - self.flash_timer * 0.6)
            if self.flash_timer >= 1.5:
                self.flash_triggered = False
                self.glow_intensity = 0.6
        else:
            self.glow_intensity = 0.7 + 0.15 * math.sin(self.time * 1.8)

        # Update tentacle phases
        for i in range(self.num_tentacles):
            self.tentacle_phases[i] += self.tentacle_speeds[i]

        # Update oral arm phases
        for i in range(self.num_oral_arms):
            self.oral_arm_phases[i] += 0.03

        # Update particles
        self._update_particles(dt)

        sc = self.size_scale
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(x, y)
        painter.scale(sc, sc)

        # Render order: back to front
        self._draw_ambient_particles(painter)
        self._draw_outer_glow(painter)
        self._draw_tentacles(painter, speed_factor)
        self._draw_oral_arms(painter, speed_factor)
        self._draw_bell(painter)
        self._draw_bell_highlight(painter)
        self._draw_inner_glow(painter)

        painter.restore()

    # --- Particles ---

    def _update_particles(self, dt):
        """Drift particles upward and respawn dead ones."""
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt * 0.12
            p["phase"] += p["pulse_speed"] * dt
            if p["life"] <= 0 or abs(p["y"]) > 280 or abs(p["x"]) > 250:
                new = self._new_particle(near_origin=True)
                p.update(new)

    def _draw_ambient_particles(self, painter):
        """Tiny glowing dots drifting around the jellyfish."""
        painter.setPen(Qt.NoPen)
        for p in self.particles:
            pulse = 0.5 + 0.5 * math.sin(p["phase"])
            alpha = int(p["life"] * 200 * pulse * self.glow_intensity)
            if alpha < 8:
                continue
            sz = p["size"] * (0.8 + 0.4 * pulse)

            # Soft glow circle
            grad = QRadialGradient(p["x"], p["y"], sz * 2.5)
            grad.setColorAt(0.0, QColor(180, 255, 255, alpha))
            grad.setColorAt(0.5, QColor(0, 220, 255, int(alpha * 0.4)))
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QPointF(p["x"], p["y"]), sz * 2.5, sz * 2.5)

    # --- Outer glow halo ---

    def _draw_outer_glow(self, painter):
        """Large radial glow halo around the jellyfish."""
        glow_r = self.bell_radius * (3.5 + self.glow_intensity * 2.0)
        alpha_base = int(55 * self.glow_intensity)

        grad = QRadialGradient(0, -self.bell_height * 0.3, glow_r)
        grad.setColorAt(0.0, QColor(0, 230, 255, alpha_base))
        grad.setColorAt(0.3, QColor(0, 180, 230, int(alpha_base * 0.5)))
        grad.setColorAt(0.6, QColor(0, 120, 180, int(alpha_base * 0.2)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(
            QPointF(0, -self.bell_height * 0.3),
            glow_r, glow_r * 0.85
        )

    # --- Bell ---

    def _draw_bell(self, painter):
        """Draw the dome-shaped translucent bell with pulsing."""
        c = self.bell_contraction
        r = self.bell_radius
        h = self.bell_height

        # Dimensions shift with pulse
        w_factor = 1.0 - c * 0.12
        h_factor = 0.75 + c * 0.25
        bw = r * w_factor
        bh = h * h_factor

        # Dome path
        path = QPainterPath()
        top_y = -bh
        path.moveTo(-bw, 0)
        # Left curve up to apex
        path.cubicTo(-bw, -bh * 0.9, -bw * 0.3, top_y, 0, top_y)
        # Apex to right
        path.cubicTo(bw * 0.3, top_y, bw, -bh * 0.9, bw, 0)

        # Scalloped bottom margin
        scallops = 12
        for i in range(scallops + 1):
            t = i / scallops
            sx = bw - 2 * bw * t
            scallop_depth = 4 * math.sin(t * math.pi * scallops * 0.5 + self.time * 2) * (1 - abs(t - 0.5) * 2)
            sy = scallop_depth
            path.lineTo(sx, sy)

        path.closeSubpath()

        # Fill: radial gradient from bright cyan core to translucent edge
        bell_grad = QRadialGradient(0, -bh * 0.4, r * 1.3)
        core_alpha = int(130 + 70 * self.glow_intensity)
        bell_grad.setColorAt(0.0, QColor(140, 250, 255, core_alpha))
        bell_grad.setColorAt(0.35, QColor(50, 220, 245, int(core_alpha * 0.75)))
        bell_grad.setColorAt(0.7, QColor(15, 190, 230, int(core_alpha * 0.45)))
        bell_grad.setColorAt(1.0, QColor(5, 150, 190, int(core_alpha * 0.25)))

        # Outline
        edge_alpha = int(120 + 80 * self.glow_intensity)
        painter.setPen(QPen(QColor(80, 240, 255, edge_alpha), 1.5))
        painter.setBrush(QBrush(bell_grad))
        painter.drawPath(path)

    def _draw_bell_highlight(self, painter):
        """Specular highlight on the bell dome for glassy look."""
        r = self.bell_radius * 0.5
        h = self.bell_height
        cx_off = -r * 0.25
        cy_off = -h * 0.65

        highlight = QRadialGradient(cx_off, cy_off, r * 0.7)
        ha = int(70 + 50 * self.glow_intensity)
        highlight.setColorAt(0.0, QColor(255, 255, 255, ha))
        highlight.setColorAt(0.5, QColor(200, 255, 255, int(ha * 0.3)))
        highlight.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(QPointF(cx_off, cy_off), r * 0.7, r * 0.5)

    def _draw_inner_glow(self, painter):
        """Bright core glow inside the bell (the 'lantern' effect)."""
        h = self.bell_height
        core_r = self.bell_radius * 0.45
        cy = -h * 0.35

        grad = QRadialGradient(0, cy, core_r)
        ca = int(140 * self.glow_intensity)
        grad.setColorAt(0.0, QColor(200, 255, 255, ca))
        grad.setColorAt(0.3, QColor(0, 240, 255, int(ca * 0.6)))
        grad.setColorAt(0.7, QColor(0, 180, 230, int(ca * 0.2)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(0, cy), core_r, core_r * 0.8)

        # Pulsing ring at bell mid-section
        ring_alpha = int(60 + 40 * math.sin(self.time * 2.5))
        ring_r = self.bell_radius * (0.7 + 0.05 * math.sin(self.time * 2.5))
        painter.setPen(QPen(QColor(0, 240, 255, ring_alpha), 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, -h * 0.25), ring_r, ring_r * 0.35)

    # --- Tentacles ---

    def _draw_tentacles(self, painter, speed_factor):
        """Long flowing tentacles hanging from the bell margin."""
        margin_r = self.bell_radius * 0.88
        segments = 25

        for i in range(self.num_tentacles):
            # Distribute evenly along bell bottom arc
            t_angle = math.pi * (i / (self.num_tentacles - 1))  # 0 to pi (left to right)
            start_x = math.cos(math.pi - t_angle) * margin_r
            start_y = 2  # Just below bell margin

            phase = self.tentacle_phases[i]
            length = self.tentacle_lengths[i]

            points = []
            for j in range(segments + 1):
                frac = j / segments
                # Gravity pulls down
                ty = start_y + length * frac
                # Sway: multiple sine waves for organic motion
                wave1 = math.sin(phase + frac * 3.5) * 12 * frac
                wave2 = math.sin(phase * 0.6 + frac * 5.5 + i) * 5 * frac
                wave3 = math.sin(self.time * 0.4 + frac * 2 + i * 0.3) * 3 * frac
                tx = start_x + wave1 + wave2 + wave3
                points.append((tx, ty))

            # Draw segments with tapering width and fading alpha
            for j in range(len(points) - 1):
                frac = j / segments
                thickness = 2.2 * (1 - frac * 0.85)
                alpha = int((1 - frac * 0.8) * 130 * self.glow_intensity)
                if alpha < 5:
                    continue

                # Color: cyan fading to darker
                r_c = int(0 + 20 * frac)
                g_c = int(220 - 80 * frac)
                b_c = int(250 - 60 * frac)
                color = QColor(r_c, g_c, b_c, alpha)

                # Glow layer
                glow_alpha = int(alpha * 0.3)
                if glow_alpha > 3:
                    painter.setPen(QPen(
                        QColor(r_c, g_c, b_c, glow_alpha),
                        thickness * 3,
                        Qt.SolidLine, Qt.RoundCap
                    ))
                    painter.drawLine(
                        QPointF(points[j][0], points[j][1]),
                        QPointF(points[j + 1][0], points[j + 1][1])
                    )

                # Core line
                painter.setPen(QPen(color, max(0.5, thickness), Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(
                    QPointF(points[j][0], points[j][1]),
                    QPointF(points[j + 1][0], points[j + 1][1])
                )

    # --- Oral arms ---

    def _draw_oral_arms(self, painter, speed_factor):
        """Shorter, slightly thicker arms near the center of the bell underside."""
        arm_length = self.bell_radius * 0.9
        segments = 15

        for i in range(self.num_oral_arms):
            spread = (i - (self.num_oral_arms - 1) / 2) * 8
            phase = self.oral_arm_phases[i]
            start_x = spread
            start_y = 5

            points = []
            for j in range(segments + 1):
                frac = j / segments
                ty = start_y + arm_length * frac
                wave = math.sin(phase + frac * 4) * 8 * frac
                tx = start_x + wave
                points.append((tx, ty))

            for j in range(len(points) - 1):
                frac = j / segments
                thickness = 3.0 * (1 - frac * 0.7)
                alpha = int((1 - frac * 0.6) * 100 * self.glow_intensity)
                if alpha < 5:
                    continue

                color = QColor(40, 230, 255, alpha)

                # Glow
                painter.setPen(QPen(
                    QColor(20, 200, 240, int(alpha * 0.25)),
                    thickness * 2.5, Qt.SolidLine, Qt.RoundCap
                ))
                painter.drawLine(
                    QPointF(points[j][0], points[j][1]),
                    QPointF(points[j + 1][0], points[j + 1][1])
                )

                # Core
                painter.setPen(QPen(color, max(0.8, thickness), Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(
                    QPointF(points[j][0], points[j][1]),
                    QPointF(points[j + 1][0], points[j + 1][1])
                )
