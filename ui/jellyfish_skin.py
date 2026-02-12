"""
Bioluminescent Deep Sea Jellyfish Renderer
Based on Atolla wyvillei (Alarm Jellyfish) with spectacular blue light displays.

Features:
- Crown-shaped bell with deep groove
- Brilliant blue bioluminescent pinwheel flashes
- One hypertrophied (extra-long) trailing tentacle
- Pulsing jet propulsion swimming
- Translucent tentacles with flowing animation
- Reactive light display when interacted with
"""

import math
import random
import numpy as np
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QRadialGradient,
    QLinearGradient, QBrush, QPen
)
from PySide6.QtCore import QPointF, Qt


class BioluminescentJellyfishSkin:
    """
    Deep sea bioluminescent jellyfish renderer.
    Inspired by Atolla jellyfish - the 'Alarm Jellyfish' with spectacular light displays.
    """

    # Bioluminescence colors
    BIO_BLUE = QColor(20, 150, 255, 200)      # Electric blue
    BIO_CYAN = QColor(0, 255, 255, 180)       # Cyan
    BIO_WHITE = QColor(200, 240, 255, 160)    # Light blue-white
    
    # Deep sea jelly colors
    BELL_RED = QColor(80, 15, 25, 180)        # Deep red (appears black in deep)
    BELL_DARK = QColor(40, 8, 15, 200)        # Darker center
    TENTACLE_COLOR = QColor(120, 40, 60, 100) # Translucent red tentacles

    def __init__(self, config=None):
        self.time = 0.0
        self.pulse_phase = 0.0
        self.flash_phase = 0.0
        self.glow_intensity = 0.0
        self.flash_triggered = False
        self.flash_timer = 0.0
        
        # Animation state
        self.bell_contraction = 0.0  # 0 = relaxed, 1 = fully contracted
        self.tentacle_sway = [random.uniform(0, math.pi * 2) for _ in range(12)]
        self.trailing_tentacle_phase = 0.0
        
        # Size
        self.bell_radius = 35
        self.tentacle_length = 80
        self.trailing_tentacle_length = 200  # Extra long
        
        self.size_scale = 1.0
        self.opacity = 0.9
        self._facing_left = False
        
        if config:
            self.apply_config(config)

    def apply_config(self, config):
        fish_cfg = config.get("fish") if hasattr(config, "get") else {}
        if isinstance(fish_cfg, dict):
            self.size_scale = fish_cfg.get("size_scale", self.size_scale)

    def trigger_flash(self):
        """Trigger bioluminescent flash display."""
        self.flash_triggered = True
        self.flash_timer = 0.0
        self.glow_intensity = 1.0

    def render(self, painter, local_pos, fish_state):
        """Main render entry point."""
        x = fish_state.get("position", [0, 0])[0]
        y = fish_state.get("position", [0, 0])[1]
        angle = fish_state.get("facing_angle", 0)
        self.update_and_render(painter, x, y, angle, fish_state)

    def update_and_render(self, painter, x, y, angle, fish_state):
        """Render the bioluminescent jellyfish.
        
        NOTE: Jellyfish stay UPRIGHT - they don't roll over like fish!
        Tentacles always hang DOWN due to gravity.
        Only the bell pulses for propulsion.
        """
        vx = fish_state.get("velocity", [0, 0])[0]
        vy = fish_state.get("velocity", [0, 0])[1]
        speed = math.hypot(vx, vy)
        mood = fish_state.get("mood", 80)
        
        dt = 0.033
        speed_factor = min(speed / 100.0, 2.0)
        
        # Update animation
        self.time += dt
        
        # Bell pulsing for swimming (0.5-1 Hz)
        # Real jellyfish pulse their bell to push water out for propulsion
        pulse_speed = 0.08 + speed_factor * 0.04
        self.pulse_phase += pulse_speed
        self.bell_contraction = (math.sin(self.pulse_phase) + 1) / 2  # 0 to 1
        
        # Flash animation
        if self.flash_triggered:
            self.flash_timer += dt * 8  # Fast flash
            self.glow_intensity = max(0, 1.0 - self.flash_timer)
            if self.flash_timer >= 1.0:
                self.flash_triggered = False
                self.glow_intensity = 0.0
        else:
            # Subtle ambient glow pulsing
            self.glow_intensity = 0.15 + 0.1 * math.sin(self.time * 2)
        
        # Trailing tentacle animation
        self.trailing_tentacle_phase += 0.05 + speed_factor * 0.02
        
        # Update tentacle sway (gentle drifting motion)
        for i in range(len(self.tentacle_sway)):
            self.tentacle_sway[i] += 0.03 + i * 0.01
        
        # Jellyfish orientation: ALWAYS UPRIGHT
        # Unlike fish, jellyfish don't roll over - bell stays up, tentacles stay down
        # We only use the position (x,y), not the rotation angle
        
        sc = self.size_scale
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(x, y)
        
        # Jellyfish stays upright - NO rotation based on movement angle
        # Only scale for size, no flipping or rotation
        painter.scale(sc, sc)
        
        # Render back to front
        self._draw_bioluminescent_glow(painter)
        self._draw_trailing_tentacle(painter, speed_factor)
        self._draw_tentacles(painter, speed_factor)
        self._draw_oral_arms(painter, speed_factor)
        self._draw_bell(painter, speed_factor)
        self._draw_crown_groove(painter)
        self._draw_bioluminescent_rings(painter)
        self._draw_rhopalia(painter)  # Sensory organs
        
        painter.restore()

    def _draw_bioluminescent_glow(self, painter):
        """Outer glow effect for bioluminescence."""
        if self.glow_intensity < 0.01:
            return
        
        # Expanding glow aura
        glow_radius = self.bell_radius * (2.0 + self.glow_intensity * 2)
        alpha = int(60 * self.glow_intensity)
        
        gradient = QRadialGradient(0, 0, glow_radius)
        gradient.setColorAt(0.0, QColor(0, 200, 255, alpha))
        gradient.setColorAt(0.4, QColor(0, 150, 255, int(alpha * 0.5)))
        gradient.setColorAt(0.7, QColor(50, 100, 255, int(alpha * 0.2)))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), glow_radius, glow_radius * 0.8)

    def _draw_bell(self, painter, speed_factor):
        """
        Draw the bell (umbrella) with pulsing contraction.
        Atolla has a crown-like shape with deep groove.
        """
        # Bell shape changes with contraction
        contraction = self.bell_contraction
        
        # Base bell dimensions
        base_radius = self.bell_radius
        # Bell flattens when contracted (jet propulsion)
        height_factor = 0.6 + contraction * 0.4  # Taller when relaxed
        width_factor = 1.0 - contraction * 0.15   # Narrower when contracted
        
        # Create bell path
        bell_path = QPainterPath()
        
        # Top of bell
        top_y = -base_radius * height_factor
        bell_path.moveTo(0, top_y)
        
        # Right side with crown groove
        # Crown groove creates indent around middle
        groove_depth = 8 * (1 - contraction * 0.5)
        groove_y = top_y + base_radius * height_factor * 0.5
        
        # Upper curve
        ctrl1_x = base_radius * width_factor * 0.5
        ctrl1_y = top_y
        ctrl2_x = base_radius * width_factor
        ctrl2_y = groove_y - groove_depth
        bell_path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, 
                         base_radius * width_factor, groove_y)
        
        # Groove indent
        bell_path.quadTo(base_radius * width_factor * 0.85, groove_y + groove_depth * 0.5,
                        base_radius * width_factor * 0.9, groove_y + groove_depth)
        
        # Lower curve to margin
        margin_y = 0
        bell_path.cubicTo(base_radius * width_factor * 0.9, groove_y + groove_depth,
                         base_radius * width_factor, margin_y - 5,
                         base_radius * width_factor * 0.95, margin_y)
        
        # Bottom margin (slightly scalloped)
        for i in range(4):
            t = i / 3
            seg_x = base_radius * width_factor * (1 - t * 2)
            scallop = 3 * math.sin(t * math.pi)
            if i == 0:
                bell_path.lineTo(seg_x, margin_y + scallop)
            else:
                bell_path.quadTo(seg_x + 5, margin_y + scallop - 2, seg_x, margin_y + scallop)
        
        # Left side (mirror)
        bell_path.cubicTo(-base_radius * width_factor * 0.95, margin_y,
                         -base_radius * width_factor, margin_y - 5,
                         -base_radius * width_factor * 0.9, groove_y + groove_depth)
        
        bell_path.quadTo(-base_radius * width_factor * 0.85, groove_y + groove_depth * 0.5,
                        -base_radius * width_factor, groove_y)
        
        bell_path.cubicTo(-base_radius * width_factor, groove_y - groove_depth,
                         -base_radius * width_factor * 0.5, top_y,
                         0, top_y)
        
        bell_path.closeSubpath()
        
        # Bell gradient - deep red to dark
        bell_grad = QRadialGradient(0, top_y * 0.3, base_radius * 1.2)
        bell_grad.setColorAt(0.0, self.BELL_DARK)
        bell_grad.setColorAt(0.5, self.BELL_RED)
        bell_grad.setColorAt(0.85, QColor(100, 25, 40, 150))
        bell_grad.setColorAt(1.0, QColor(120, 40, 60, 100))
        
        painter.setPen(QPen(QColor(60, 15, 25, 150), 1))
        painter.setBrush(QBrush(bell_grad))
        painter.drawPath(bell_path)
        
        # Inner bell surface (translucent)
        inner_path = QPainterPath()
        inner_radius = base_radius * 0.7
        inner_path.addEllipse(QPointF(0, -base_radius * height_factor * 0.3), 
                             inner_radius, inner_radius * 0.5)
        
        inner_grad = QRadialGradient(0, -base_radius * height_factor * 0.3, inner_radius)
        inner_grad.setColorAt(0.0, QColor(40, 10, 20, 120))
        inner_grad.setColorAt(1.0, QColor(60, 20, 30, 80))
        
        painter.setBrush(QBrush(inner_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(inner_path)

    def _draw_crown_groove(self, painter):
        """Draw the distinctive crown groove around bell middle."""
        groove_y = -self.bell_radius * 0.3
        groove_width = self.bell_radius * 0.95
        
        # Groove shadow
        groove_path = QPainterPath()
        groove_path.moveTo(-groove_width, groove_y - 3)
        groove_path.quadTo(0, groove_y + 5, groove_width, groove_y - 3)
        groove_path.lineTo(groove_width, groove_y + 3)
        groove_path.quadTo(0, groove_y + 8, -groove_width, groove_y + 3)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(30, 8, 15, 180))
        painter.drawPath(groove_path)
        
        # Bioluminescent rim of groove
        if self.glow_intensity > 0.05:
            alpha = int(150 * self.glow_intensity)
            painter.setPen(QPen(QColor(0, 200, 255, alpha), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(groove_path)

    def _draw_bioluminescent_rings(self, painter):
        """
        Draw the spectacular blue pinwheel flash pattern.
        Atolla produces circular waves of blue light when threatened.
        """
        if self.glow_intensity < 0.1:
            # Subtle ambient ring
            alpha = int(30 + 20 * math.sin(self.time * 3))
            painter.setPen(QPen(QColor(0, 180, 255, alpha), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, -self.bell_radius * 0.3), 
                              self.bell_radius * 0.6, self.bell_radius * 0.4)
            return
        
        # Flash mode - expanding rings
        num_rings = 4
        for i in range(num_rings):
            ring_progress = (self.flash_timer + i * 0.25) % 1.0
            ring_radius = self.bell_radius * (0.3 + ring_progress * 0.8)
            alpha = int(200 * (1 - ring_progress) * self.glow_intensity)
            
            if alpha < 5:
                continue
            
            # Electric blue ring
            painter.setPen(QPen(QColor(20, 220, 255, alpha), 3 - ring_progress * 2))
            painter.setBrush(Qt.NoBrush)
            
            # Slightly elliptical
            painter.drawEllipse(QPointF(0, -self.bell_radius * 0.3),
                              ring_radius, ring_radius * 0.7)
        
        # Center glow during flash
        center_glow = QRadialGradient(0, -self.bell_radius * 0.3, self.bell_radius * 0.5)
        center_glow.setColorAt(0.0, QColor(100, 240, 255, int(100 * self.glow_intensity)))
        center_glow.setColorAt(0.5, QColor(0, 200, 255, int(60 * self.glow_intensity)))
        center_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(center_glow))
        painter.drawEllipse(QPointF(0, -self.bell_radius * 0.3),
                          self.bell_radius * 0.5, self.bell_radius * 0.4)

    def _draw_rhopalia(self, painter):
        """Draw rhopalia - sensory organs around bell margin."""
        num_rhopalia = 8
        margin_radius = self.bell_radius * 0.9
        
        for i in range(num_rhopalia):
            angle = (i / num_rhopalia) * 2 * math.pi
            rx = math.cos(angle) * margin_radius
            ry = math.sin(angle) * margin_radius * 0.3  # Flattened
            
            # Rhopalium glows during flash
            alpha = int(100 + 155 * self.glow_intensity)
            painter.setBrush(QColor(0, 220, 255, alpha))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(rx, ry), 2.5, 2)

    def _draw_oral_arms(self, painter, speed_factor):
        """Draw oral arms - frilled appendages near mouth."""
        num_arms = 4
        arm_length = self.bell_radius * 0.8
        
        for i in range(num_arms):
            side = 1 if i % 2 == 0 else -1
            arm_offset = side * (5 + i * 3)
            
            # Arm sways
            sway = math.sin(self.time * 1.5 + i) * 8
            
            arm_path = QPainterPath()
            arm_path.moveTo(arm_offset, 5)
            
            # Curved arm
            ctrl_x = arm_offset + sway * 0.5
            ctrl_y = arm_length * 0.5
            end_x = arm_offset + sway
            end_y = arm_length
            
            arm_path.quadTo(ctrl_x, ctrl_y, end_x, end_y)
            
            # Frilled edge
            for j in range(5):
                t = j / 4
                fx = arm_offset + (end_x - arm_offset) * t + side * 3 * math.sin(t * math.pi)
                fy = 5 + (end_y - 5) * t
                arm_path.lineTo(fx, fy)
            
            arm_path.lineTo(end_x - side * 4, end_y)
            arm_path.quadTo(ctrl_x - side * 4, ctrl_y, arm_offset - side * 3, 5)
            
            # Arm gradient
            arm_grad = QLinearGradient(arm_offset, 5, end_x, end_y)
            arm_grad.setColorAt(0.0, QColor(100, 40, 60, 150))
            arm_grad.setColorAt(0.5, QColor(80, 30, 50, 120))
            arm_grad.setColorAt(1.0, QColor(60, 20, 40, 80))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(arm_grad))
            painter.drawPath(arm_path)

    def _draw_tentacles(self, painter, speed_factor):
        """Draw marginal tentacles."""
        num_tentacles = 10
        margin_radius = self.bell_radius * 0.9
        
        for i in range(num_tentacles):
            angle = (i / num_tentacles) * 2 * math.pi
            start_x = math.cos(angle) * margin_radius
            start_y = math.sin(angle) * margin_radius * 0.3
            
            # Tentacle sways with phase offset
            tentacle_phase = self.tentacle_sway[i % len(self.tentacle_sway)]
            sway = math.sin(tentacle_phase) * 10
            
            tentacle_length = self.tentacle_length * (0.8 + 0.4 * math.sin(i * 0.7))
            
            # Draw tentacle as curved line with varying thickness
            points = []
            segments = 15
            for j in range(segments + 1):
                t = j / segments
                tx = start_x + sway * t * t  # More sway at tip
                ty = start_y + tentacle_length * t
                # Undulation
                undulation = math.sin(tentacle_phase + t * 4) * 3 * t
                tx += undulation
                points.append((tx, ty))
            
            # Draw with tapering thickness
            for j in range(len(points) - 1):
                t = j / segments
                thickness = 2.5 * (1 - t * 0.8)  # Taper to tip
                alpha = int(120 * (1 - t * 0.7))
                
                painter.setPen(QPen(QColor(140, 60, 80, alpha), thickness))
                painter.drawLine(QPointF(points[j][0], points[j][1]),
                               QPointF(points[j + 1][0], points[j + 1][1]))

    def _draw_trailing_tentacle(self, painter, speed_factor):
        """
        Draw the hypertrophied (extra-long) trailing tentacle.
        This is the signature feature of Atolla jellyfish.
        """
        # Starts from bell margin
        start_angle = math.pi * 0.7  # Back-right
        start_x = math.cos(start_angle) * self.bell_radius * 0.9
        start_y = math.sin(start_angle) * self.bell_radius * 0.3
        
        tentacle_length = self.trailing_tentacle_length * (0.9 + 0.2 * math.sin(self.time * 0.5))
        
        # Create flowing tentacle path
        points = []
        segments = 30
        
        for i in range(segments + 1):
            t = i / segments
            
            # Base curve
            base_x = start_x
            base_y = start_y + tentacle_length * t
            
            # Flowing motion (sine waves)
            wave1 = math.sin(self.trailing_tentacle_phase + t * 3) * 15 * t
            wave2 = math.sin(self.trailing_tentacle_phase * 0.7 + t * 5) * 8 * t
            wave3 = math.sin(self.time * 0.3 + t * 2) * 5 * t
            
            tx = base_x + wave1 + wave2 + wave3
            ty = base_y
            
            points.append((tx, ty))
        
        # Draw with extreme taper
        for i in range(len(points) - 1):
            t = i / segments
            thickness = 4.0 * (1 - t * 0.95)  # Very thin at tip
            alpha = int(100 * (1 - t * 0.6))
            
            # Bioluminescent tip during flash
            if t > 0.8 and self.glow_intensity > 0.1:
                glow_alpha = int(200 * self.glow_intensity * (t - 0.8) * 5)
                painter.setPen(QPen(QColor(50, 230, 255, glow_alpha), thickness + 2))
                painter.drawLine(QPointF(points[i][0], points[i][1]),
                               QPointF(points[i + 1][0], points[i + 1][1]))
            
            painter.setPen(QPen(QColor(160, 70, 90, alpha), max(0.5, thickness)))
            painter.drawLine(QPointF(points[i][0], points[i][1]),
                           QPointF(points[i + 1][0], points[i + 1][1]))
        
        # Bioluminescent nodes along tentacle
        if self.glow_intensity > 0.05:
            for i in range(3, 8):
                t = i / 10
                node_x = points[int(t * segments)][0]
                node_y = points[int(t * segments)][1]
                node_alpha = int(150 * self.glow_intensity * (1 - t))
                
                painter.setBrush(QColor(0, 220, 255, node_alpha))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(node_x, node_y), 2, 2)
