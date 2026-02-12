"""
Iridescent Jellyfish v3.0 - Deep Sea Bioluminescent Creature
Rainbow-shifting opalescent body with realistic deep sea light effects
Inspired by Atolla wyvillei and deep sea comb jellies
"""

import math
import random
from typing import List, Tuple
from dataclasses import dataclass, field
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QConicalGradient, QPen, QBrush
)
from PySide6.QtWidgets import QWidget


@dataclass
class LightParticle:
    """Bioluminescent light particle drifting in water"""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    hue: float
    life: float = 1.0
    pulse_phase: float = 0.0
    
    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 5 * dt  # Rise up
        self.life -= dt * 0.3
        self.pulse_phase += dt * 3


@dataclass
class TentacleSegment:
    """Single segment of tentacle with light trail"""
    x: float
    y: float
    width: float
    glow_intensity: float = 0.0


class IridescentJellyfish(QWidget):
    """
    Deep sea iridescent jellyfish with rainbow bioluminescence
    Features:
    - Opalescent/iridescent bell that shifts colors with movement
    - Transparent gelatinous body with internal light refraction
    - Bioluminescent light particles and trails
    - Crown groove with spectacular light show (Atolla-style)
    - Rainbow gradient tentacles
    """
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        
        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Position
        self.x = 1920.0
        self.y = 540.0
        
        # Movement
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.pulse_phase = 0.0
        
        # Animation
        self.time = 0.0
        self.bell_pulse = 0.0
        self.tentacle_phase = 0.0
        self.iridescent_phase = 0.0
        
        # Visual state
        self.bell_size = 60.0
        self.flash_active = False
        self.flash_intensity = 0.0
        self.flash_rings = []
        
        # Collections
        self.light_particles: List[LightParticle] = []
        self.tentacles: List[List[TentacleSegment]] = []
        self._init_tentacles()
        
        # Iridescent colors - shifting rainbow
        self.base_hue = 260  # Purple base
        self.iridescent_shift = 0.0
        
        self.resize(300, 350)
        self.move(int(self.x - 150), int(self.y - 175))
    
    def _init_tentacles(self):
        """Initialize tentacle segments"""
        # 8 marginal tentacles + 1 hypertrophied trailing tentacle
        for i in range(9):
            segments = []
            num_segments = 25 if i < 8 else 40  # Longer trailing tentacle
            for j in range(num_segments):
                segments.append(TentacleSegment(
                    x=0, y=0, 
                    width=max(3, 8 - j * 0.2),
                    glow_intensity=0.0
                ))
            self.tentacles.append(segments)
    
    def trigger_flash(self):
        """Trigger spectacular bioluminescent flash (Atolla alarm response)"""
        self.flash_active = True
        self.flash_intensity = 1.0
        
        # Create expanding light rings
        self.flash_rings = [
            {'radius': 20, 'alpha': 255, 'width': 3},
            {'radius': 40, 'alpha': 200, 'width': 2.5},
            {'radius': 60, 'alpha': 150, 'width': 2},
        ]
        
        # Burst of light particles
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(30, 80)
            hue = random.choice([200, 260, 280, 300, 320])  # Blue-purple-pink
            self.light_particles.append(LightParticle(
                x=self.x,
                y=self.y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed - 20,
                size=random.uniform(3, 8),
                hue=hue,
                life=1.5
            ))
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update jellyfish state"""
        self.time += dt
        self.tentacle_phase += dt * 2
        self.iridescent_phase += dt * 1.5
        
        # Smooth movement toward target
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 10:
            self.vx += (dx / dist) * 30 * dt
            self.vy += (dy / dist) * 30 * dt
        
        # Gentle drift
        self.vx += math.sin(self.time * 0.5) * 5 * dt
        self.vy += math.cos(self.time * 0.3) * 5 * dt
        
        # Damping
        self.vx *= 0.95
        self.vy *= 0.95
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Bell pulsing (breathing motion)
        self.bell_pulse = math.sin(self.time * 1.5) * 0.1 + 1.0
        
        # Iridescent color shifting
        self.iridescent_shift = (self.iridescent_shift + dt * 30) % 360
        
        # Update flash
        if self.flash_active:
            self.flash_intensity -= dt * 0.8
            if self.flash_intensity <= 0:
                self.flash_active = False
                self.flash_intensity = 0
            
            # Update flash rings
            for ring in self.flash_rings:
                ring['radius'] += dt * 150
                ring['alpha'] = int(ring['alpha'] * 0.95)
                ring['width'] *= 0.98
        
        # Update light particles
        for particle in self.light_particles[:]:
            particle.update(dt)
            if particle.life <= 0:
                self.light_particles.remove(particle)
        
        # Random bioluminescent particle emission
        if random.random() < 0.1:
            self._emit_light_particle()
        
        # Update tentacle positions
        self._update_tentacles(dt)
        
        self.move(int(self.x - 150), int(self.y - 175))
        self.update()
    
    def _emit_light_particle(self):
        """Emit a drifting bioluminescent particle"""
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(20, 60)
        self.light_particles.append(LightParticle(
            x=self.x + math.cos(angle) * dist,
            y=self.y + math.sin(angle) * dist + 50,
            vx=random.uniform(-10, 10),
            vy=random.uniform(-20, -40),
            size=random.uniform(2, 5),
            hue=(self.base_hue + random.uniform(-30, 30)) % 360,
            life=random.uniform(0.8, 1.5)
        ))
    
    def _update_tentacles(self, dt: float):
        """Update tentacle segment positions with wave motion"""
        for i, tentacle in enumerate(self.tentacles):
            # Tentacle base position around bell edge
            angle_offset = (i / 8) * math.pi * 2 if i < 8 else 0
            base_angle = math.pi / 2 + angle_offset
            
            # Base position
            base_x = self.x + math.cos(base_angle) * 45 * self.bell_pulse
            base_y = self.y + math.sin(base_angle) * 35 * self.bell_pulse + 40
            
            # Trailing tentacle at back
            if i == 8:
                base_x = self.x
                base_y = self.y + 50
            
            for j, segment in enumerate(tentacle):
                # Wave motion propagating down tentacle
                wave = math.sin(self.tentacle_phase + j * 0.3 + i * 0.5) * (j * 1.5)
                wave2 = math.cos(self.tentacle_phase * 0.7 + j * 0.2) * (j * 0.8)
                
                # Trailing tentacle has more dramatic motion
                if i == 8:
                    wave *= 1.5
                    wave2 *= 2
                
                segment.x = base_x + wave + math.sin(self.time + j * 0.1) * 3
                segment.y = base_y + j * 6 + wave2 * 0.3
                
                # Glow based on movement and flash
                segment.glow_intensity = 0.3 + self.flash_intensity * 0.7
    
    def paintEvent(self, event):
        """Render iridescent jellyfish"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        cx = 150
        cy = 150
        
        # Draw bioluminescent particles first (behind jellyfish)
        self._draw_light_particles(painter)
        
        # Draw flash rings
        if self.flash_active:
            self._draw_flash_rings(painter, cx, cy)
        
        # Draw tentacles (behind bell)
        self._draw_tentacles(painter)
        
        # Draw main bell body
        self._draw_iridescent_bell(painter, cx, cy)
        
        # Draw internal structures
        self._draw_internal_glow(painter, cx, cy)
        
        # Draw crown groove (Atolla feature)
        self._draw_crown_groove(painter, cx, cy)
    
    def _draw_light_particles(self, painter: QPainter):
        """Draw drifting bioluminescent particles"""
        for particle in self.light_particles:
            px = particle.x - self.x + 150
            py = particle.y - self.y + 150
            
            if not (0 <= px <= 300 and 0 <= py <= 350):
                continue
            
            # Pulsing glow
            pulse = 0.7 + 0.3 * math.sin(particle.pulse_phase)
            alpha = int(particle.life * 200 * pulse)
            
            # Iridescent color
            color = QColor.fromHsv(int(particle.hue) % 360, 200, 255, alpha)
            
            # Multi-layer glow
            for i in range(3):
                size = particle.size * (2 + i * 0.8)
                layer_alpha = int(alpha * (0.5 - i * 0.15))
                
                gradient = QRadialGradient(px, py, size)
                gradient.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), layer_alpha))
                gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
                
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(px - size), int(py - size), int(size * 2), int(size * 2))
    
    def _draw_flash_rings(self, painter: QPainter, cx: float, cy: float):
        """Draw expanding flash rings"""
        for ring in self.flash_rings:
            if ring['alpha'] > 10:
                # Iridescent ring colors
                hue = (self.iridescent_shift + ring['radius'] * 2) % 360
                color = QColor.fromHsv(int(hue), 150, 255, int(ring['alpha']))
                
                painter.setPen(QPen(color, ring['width']))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(
                    int(cx - ring['radius']), 
                    int(cy - ring['radius'] * 0.8),
                    int(ring['radius'] * 2),
                    int(ring['radius'] * 1.6)
                )
    
    def _draw_tentacles(self, painter: QPainter):
        """Draw rainbow gradient tentacles with light trails"""
        for i, tentacle in enumerate(self.tentacles):
            if len(tentacle) < 2:
                continue
            
            # Each tentacle has different hue
            base_hue = (self.iridescent_shift + i * 40) % 360
            
            # Draw segments with gradient
            for j in range(len(tentacle) - 1):
                seg1 = tentacle[j]
                seg2 = tentacle[j + 1]
                
                # Position relative to widget
                x1 = seg1.x - self.x + 150
                y1 = seg1.y - self.y + 150
                x2 = seg2.x - self.x + 150
                y2 = seg2.y - self.y + 150
                
                # Gradient along tentacle length
                progress = j / len(tentacle)
                hue = (base_hue + progress * 60) % 360
                
                # Alpha fades toward tip
                alpha = int((1 - progress) * 180 * seg1.glow_intensity)
                
                # Width tapers
                width = max(1, seg1.width * (1 - progress * 0.7))
                
                color = QColor.fromHsv(int(hue), 180, 255, alpha)
                
                # Glow effect
                glow_width = width * 3
                glow_alpha = int(alpha * 0.3)
                glow_color = QColor.fromHsv(int(hue), 150, 255, glow_alpha)
                
                # Draw glow
                painter.setPen(QPen(glow_color, glow_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                
                # Draw core
                painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_iridescent_bell(self, painter: QPainter, cx: float, cy: float):
        """Draw the main bell with iridescent/opalescent effect"""
        
        # Bell dimensions with pulsing
        bell_w = 70 * self.bell_pulse
        bell_h = 55 * self.bell_pulse
        
        # Create iridescent gradient - shifting rainbow
        # Main body gradient (conical for iridescent effect)
        bell_gradient = QConicalGradient(cx, cy, self.iridescent_shift)
        
        # Rainbow iridescent colors
        colors = [
            (0.0, QColor(150, 100, 255, 180)),    # Purple
            (0.15, QColor(100, 150, 255, 180)),   # Blue
            (0.3, QColor(100, 255, 200, 180)),    # Cyan
            (0.45, QColor(150, 255, 150, 180)),   # Green
            (0.6, QColor(255, 255, 100, 180)),    # Yellow
            (0.75, QColor(255, 150, 100, 180)),   # Orange
            (0.9, QColor(255, 100, 150, 180)),    # Pink
            (1.0, QColor(150, 100, 255, 180)),    # Purple
        ]
        
        for pos, color in colors:
            # Add flash intensity
            flash_boost = int(self.flash_intensity * 50)
            boosted = QColor(
                min(255, color.red() + flash_boost),
                min(255, color.green() + flash_boost),
                min(255, color.blue() + flash_boost),
                color.alpha()
            )
            bell_gradient.setColorAt(pos, boosted)
        
        # Bell shape (semi-circle with ruffled edge)
        bell_path = QPainterPath()
        
        # Top dome
        bell_path.moveTo(cx - bell_w, cy + 20)
        bell_path.cubicTo(
            cx - bell_w, cy - bell_h * 1.2,
            cx + bell_w, cy - bell_h * 1.2,
            cx + bell_w, cy + 20
        )
        
        # Ruffled bottom edge (marginal lappets)
        num_lappets = 16
        for i in range(num_lappets + 1):
            t = i / num_lappets
            angle = math.pi * t
            base_x = cx + math.cos(math.pi - angle) * bell_w
            base_y = cy + 20
            
            # Ruffle effect
            ruffle = math.sin(i * 2 + self.time * 3) * 5
            lappet_x = base_x + ruffle * 0.3
            lappet_y = base_y + abs(ruffle)
            
            if i == 0:
                bell_path.lineTo(lappet_x, lappet_y)
            else:
                # Control points for smooth ruffle
                prev_t = (i - 1) / num_lappets
                prev_angle = math.pi * prev_t
                cpx = cx + math.cos(math.pi - (prev_angle + angle) / 2) * (bell_w + 8)
                cpy = cy + 20 + 5
                bell_path.quadTo(cpx, cpy, lappet_x, lappet_y)
        
        bell_path.closeSubpath()
        
        # Draw bell glow (outer)
        glow_gradient = QRadialGradient(cx, cy, bell_w * 1.5)
        glow_hue = int(self.iridescent_shift) % 360
        glow_color = QColor.fromHsv(glow_hue, 150, 255, 60)
        glow_gradient.setColorAt(0.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 80 + int(self.flash_intensity * 100)))
        glow_gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - bell_w * 1.5), int(cy - bell_h), int(bell_w * 3), int(bell_h * 3))
        
        # Draw bell body
        painter.setBrush(QBrush(bell_gradient))
        
        # Semi-transparent outline
        outline_color = QColor.fromHsv(int(self.iridescent_shift) % 360, 200, 255, 120)
        pen_width = 1.5 + self.flash_intensity * 2
        painter.setPen(QPen(outline_color, pen_width))
        painter.drawPath(bell_path)
        
        # Inner highlight (gelatinous look)
        highlight_gradient = QRadialGradient(cx - 15, cy - 10, bell_w * 0.6)
        highlight_gradient.setColorAt(0.0, QColor(255, 255, 255, 100 + int(self.flash_intensity * 100)))
        highlight_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(highlight_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - bell_w * 0.5), int(cy - bell_h * 0.5), int(bell_w), int(bell_h * 0.8))
    
    def _draw_internal_glow(self, painter: QPainter, cx: float, cy: float):
        """Draw internal bioluminescent structures"""
        
        # Central gastrovascular cavity glow
        glow_size = 25 + math.sin(self.time * 2) * 3
        glow_hue = (self.iridescent_shift + 180) % 360
        
        cavity_gradient = QRadialGradient(cx, cy + 10, glow_size)
        cavity_gradient.setColorAt(0.0, QColor.fromHsv(int(glow_hue), 100, 255, 150 + int(self.flash_intensity * 100)))
        cavity_gradient.setColorAt(0.5, QColor.fromHsv(int(glow_hue), 150, 255, 80))
        cavity_gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(cavity_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - glow_size), int(cy + 10 - glow_size), int(glow_size * 2), int(glow_size * 2))
        
        # Radial canals (lines from center)
        num_canals = 8
        for i in range(num_canals):
            angle = (i / num_canals) * math.pi * 2 + self.time * 0.5
            length = 25 + math.sin(self.time + i) * 3
            
            x1 = cx + math.cos(angle) * 8
            y1 = cy + 10 + math.sin(angle) * 6
            x2 = cx + math.cos(angle) * length
            y2 = cy + 10 + math.sin(angle) * length * 0.6
            
            canal_hue = (self.iridescent_shift + i * 45) % 360
            canal_color = QColor.fromHsv(int(canal_hue), 180, 255, 100)
            
            painter.setPen(QPen(canal_color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_crown_groove(self, painter: QPainter, cx: float, cy: float):
        """Draw the crown groove - signature Atolla feature with spectacular lights"""
        
        # Crown groove is a deep depression in the bell with lights
        groove_w = 35
        groove_h = 20
        
        # Shifting rainbow colors for crown
        crown_hue = int(self.iridescent_shift) % 360
        
        # Crown lights (rhopalia - sensory organs)
        num_lights = 6
        for i in range(num_lights):
            angle = (i / num_lights) * math.pi * 2 + self.time * 0.3
            light_x = cx + math.cos(angle) * 18
            light_y = cy - 5 + math.sin(angle) * 10
            
            # Each light has different color
            light_hue = (crown_hue + i * 60) % 360
            light_color = QColor.fromHsv(int(light_hue), 200, 255)
            
            # Pulsing glow
            pulse = 0.6 + 0.4 * math.sin(self.time * 4 + i)
            size = 4 + pulse * 2 + self.flash_intensity * 3
            alpha = int(150 * pulse + self.flash_intensity * 100)
            
            # Outer glow
            glow = QRadialGradient(light_x, light_y, size * 2)
            glow.setColorAt(0.0, QColor(light_color.red(), light_color.green(), light_color.blue(), alpha))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(light_x - size * 2), int(light_y - size * 2), int(size * 4), int(size * 4))
            
            # Core
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.drawEllipse(int(light_x - size * 0.5), int(light_y - size * 0.5), int(size), int(size))
        
        # Crown groove outline (iridescent line)
        groove_color = QColor.fromHsv(int(crown_hue), 150, 255, 150)
        painter.setPen(QPen(groove_color, 2.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(cx - groove_w), int(cy - groove_h - 5), int(groove_w * 2), int(groove_h * 2))


class IridescentJellyfishSkin(QWidget):
    """
    Wrapper class that provides the same interface as other skins
    for compatibility with the main application
    """
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        
        # Create the actual jellyfish
        self.jellyfish = IridescentJellyfish(config, self)
        self.jellyfish.show()
        
        # Forward attributes
        self.x = self.jellyfish.x
        self.y = self.jellyfish.y
    
    def trigger_flash(self):
        """Trigger bioluminescent flash"""
        self.jellyfish.trigger_flash()
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update jellyfish state"""
        self.jellyfish.update_state(dt, target_x, target_y)
        self.x = self.jellyfish.x
        self.y = self.jellyfish.y
    
    def move(self, x, y):
        """Override move to update jellyfish"""
        super().move(x, y)
        if hasattr(self, 'jellyfish'):
            self.jellyfish.move(x, y)
    
    def show(self):
        """Show both widgets"""
        super().show()
        if hasattr(self, 'jellyfish'):
            self.jellyfish.show()
    
    def hide(self):
        """Hide both widgets"""
        super().hide()
        if hasattr(self, 'jellyfish'):
            self.jellyfish.hide()
