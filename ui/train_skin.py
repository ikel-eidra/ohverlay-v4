"""
Desktop Train v1.0 - Non-Biological Object
Tiny train that travels along desktop edges
"""

import math
import random
from typing import List, Tuple
from dataclasses import dataclass, field
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QPen, QBrush
)
from PySide6.QtWidgets import QWidget


@dataclass
class SmokeParticle:
    """Steam/smoke from chimney"""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    life: float = 1.0
    gray: int = 200
    
    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.size += dt * 5
        self.life -= dt * 0.4
        self.gray = min(255, self.gray + int(dt * 30))


class DesktopTrain(QWidget):
    """
    Charming desktop train that travels along screen edges
    Perfect for taskbar area or moving between monitors
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
        
        # Track system - train follows screen edges
        self.track_points = [
            (100, 1000),    # Bottom left area
            (3740, 1000),   # Bottom right
            (3740, 80),     # Top right
            (100, 80),      # Top left
        ]
        self.current_segment = 0
        self.segment_progress = 0.0
        
        # Position
        self.x = self.track_points[0][0]
        self.y = self.track_points[0][1]
        self.angle = 0.0
        
        # Movement
        self.speed = 80.0
        self.direction = 1  # 1 or -1
        
        # Visual
        self.scale = 0.6
        self.wheel_rotation = 0.0
        self.smoke_particles: List[SmokeParticle] = []
        self.chuff_timer = 0.0
        
        # Colors - classic steam locomotive
        self.body_color = QColor(30, 40, 50)  # Black
        self.boiler_color = QColor(50, 50, 55)
        self.gold_color = QColor(200, 170, 80)
        self.red_color = QColor(160, 40, 40)
        
        # Headlight
        self.headlight_on = True
        self.headlight_angle = 0.0
        
        self.time = 0.0
        self.resize(120, 80)
        self.move(int(self.x - 60), int(self.y - 40))
    
    def update_state(self, dt: float, target_x: float = None, target_y: float = None):
        """Update train position along track"""
        self.time += dt
        
        # Get current segment
        p1 = self.track_points[self.current_segment]
        p2 = self.track_points[(self.current_segment + 1) % len(self.track_points)]
        
        # Calculate segment direction
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        segment_length = math.sqrt(dx*dx + dy*dy)
        
        if segment_length > 0:
            # Move along segment
            self.segment_progress += (self.speed * dt) / segment_length
            
            # Calculate position
            self.x = p1[0] + dx * self.segment_progress
            self.y = p1[1] + dy * self.segment_progress
            
            # Calculate angle
            self.angle = math.atan2(dy, dx)
            
            # Update wheels
            self.wheel_rotation += (self.speed * dt * 0.5)
        
        # Move to next segment
        if self.segment_progress >= 1.0:
            self.segment_progress = 0.0
            self.current_segment = (self.current_segment + 1) % len(self.track_points)
        
        # Generate smoke
        self.chuff_timer += dt
        if self.chuff_timer > 0.4:
            self.chuff_timer = 0.0
            self._emit_smoke()
        
        # Update smoke
        for particle in self.smoke_particles[:]:
            particle.update(dt)
            if particle.life <= 0:
                self.smoke_particles.remove(particle)
        
        self.move(int(self.x - 60), int(self.y - 40))
        self.update()
    
    def _emit_smoke(self):
        """Emit smoke particles from chimney"""
        # Calculate chimney position based on angle
        offset_x = math.cos(self.angle) * 25
        offset_y = math.sin(self.angle) * 25
        
        for _ in range(3):
            particle = SmokeParticle(
                x=self.x + offset_x,
                y=self.y + offset_y - 35 * self.scale,
                vx=random.uniform(-20, 20) - math.cos(self.angle) * 30,
                vy=random.uniform(-40, -80),
                size=random.uniform(4, 8)
            )
            self.smoke_particles.append(particle)
    
    def paintEvent(self, event):
        """Render train"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Draw smoke (behind train)
        self._draw_smoke(painter)
        
        # Draw train
        self._draw_train(painter)
    
    def _draw_smoke(self, painter: QPainter):
        """Draw steam/smoke particles"""
        for particle in self.smoke_particles:
            px = particle.x - self.x + 60
            py = particle.y - self.y + 40
            
            alpha = int(150 * particle.life)
            gray = particle.gray
            
            smoke_color = QColor(gray, gray, gray, alpha)
            
            # Puffy smoke
            gradient = QRadialGradient(px, py, particle.size)
            gradient.setColorAt(0.0, smoke_color)
            gradient.setColorAt(1.0, QColor(gray, gray, gray, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(px - particle.size), int(py - particle.size),
                               int(particle.size * 2), int(particle.size * 2))
    
    def _draw_train(self, painter: QPainter):
        """Draw steam locomotive"""
        cx = 60
        cy = 40
        
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(math.degrees(self.angle))
        painter.scale(self.scale, self.scale)
        
        # Shadow
        painter.save()
        painter.translate(8, 8)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(-50, -20, 100, 40, 5, 5)
        painter.restore()
        
        # Main boiler (cylinder)
        boiler_gradient = QLinearGradient(-30, -15, 30, 15)
        boiler_gradient.setColorAt(0.0, self.boiler_color.darker(120))
        boiler_gradient.setColorAt(0.3, self.boiler_color)
        boiler_gradient.setColorAt(0.7, self.boiler_color.lighter(110))
        boiler_gradient.setColorAt(1.0, self.boiler_color.darker(130))
        
        painter.setBrush(QBrush(boiler_gradient))
        painter.setPen(QPen(QColor(20, 25, 30), 1.5))
        painter.drawRoundedRect(-40, -15, 70, 30, 8, 8)
        
        # Gold boiler bands
        painter.setPen(QPen(self.gold_color, 2.0))
        painter.drawLine(-30, -15, -30, 15)
        painter.drawLine(0, -15, 0, 15)
        painter.drawLine(25, -15, 25, 15)
        
        # Chimney/smokestack
        chimney_gradient = QLinearGradient(15, -35, 20, -15)
        chimney_gradient.setColorAt(0.0, self.body_color.lighter(120))
        chimney_gradient.setColorAt(1.0, self.body_color)
        
        painter.setBrush(QBrush(chimney_gradient))
        painter.setPen(QPen(QColor(20, 25, 30), 1.0))
        
        # Chimney base
        painter.drawRect(10, -15, 12, 5)
        # Chimney stack
        painter.drawRect(12, -35, 8, 20)
        # Chimney top
        painter.drawEllipse(10, -38, 12, 6)
        
        # Gold band on chimney
        painter.setPen(QPen(self.gold_color, 1.5))
        painter.drawLine(12, -28, 20, -28)
        
        # Cab (back section)
        cab_gradient = QLinearGradient(-50, -25, -40, 20)
        cab_gradient.setColorAt(0.0, self.red_color.lighter(110))
        cab_gradient.setColorAt(0.5, self.red_color)
        cab_gradient.setColorAt(1.0, self.red_color.darker(120))
        
        painter.setBrush(QBrush(cab_gradient))
        painter.setPen(QPen(QColor(20, 25, 30), 1.5))
        
        # Cab box
        painter.drawRect(-55, -20, 20, 40)
        
        # Cab roof
        painter.setBrush(QBrush(QColor(40, 45, 50)))
        painter.drawRoundedRect(-58, -25, 26, 8, 3, 3)
        
        # Window
        painter.setBrush(QBrush(QColor(200, 220, 240)))
        painter.setPen(QPen(QColor(30, 35, 40), 1.0))
        painter.drawRect(-52, -15, 12, 12)
        # Window reflection
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1.0))
        painter.drawLine(-50, -13, -46, -5)
        
        # Cowcatcher (front)
        painter.setBrush(QBrush(QColor(60, 60, 65)))
        painter.setPen(QPen(QColor(30, 35, 40), 1.0))
        
        cowcatcher = QPainterPath()
        cowcatcher.moveTo(35, -12)
        cowcatcher.lineTo(45, 0)
        cowcatcher.lineTo(35, 12)
        cowcatcher.lineTo(30, 12)
        cowcatcher.lineTo(30, -12)
        cowcatcher.closeSubpath()
        painter.drawPath(cowcatcher)
        
        # Cowcatcher bars
        painter.setPen(QPen(QColor(40, 45, 50), 1.5))
        for i in range(3):
            y = -8 + i * 8
            painter.drawLine(32, int(y), 42, 0)
        
        # Wheels
        wheel_positions = [(-35, 18), (-15, 18), (15, 18)]
        
        for wx, wy in wheel_positions:
            painter.save()
            painter.translate(wx, wy)
            painter.rotate(math.degrees(self.wheel_rotation))
            
            # Wheel rim
            rim_gradient = QRadialGradient(0, 0, 10)
            rim_gradient.setColorAt(0.0, QColor(80, 85, 90))
            rim_gradient.setColorAt(0.7, QColor(50, 55, 60))
            rim_gradient.setColorAt(1.0, QColor(30, 35, 40))
            
            painter.setBrush(QBrush(rim_gradient))
            painter.setPen(QPen(QColor(20, 25, 30), 1.5))
            painter.drawEllipse(-10, -10, 20, 20)
            
            # Inner wheel
            painter.setBrush(QBrush(QColor(40, 45, 50)))
            painter.setPen(QPen(QColor(20, 25, 30), 1.0))
            painter.drawEllipse(-6, -6, 12, 12)
            
            # Spokes
            painter.setPen(QPen(QColor(100, 105, 110), 2.0))
            for i in range(4):
                angle = i * math.pi / 2
                sx = math.cos(angle) * 8
                sy = math.sin(angle) * 8
                painter.drawLine(0, 0, int(sx), int(sy))
            
            # Center hub
            painter.setBrush(QBrush(self.gold_color))
            painter.setPen(QPen(QColor(150, 130, 60), 1.0))
            painter.drawEllipse(-3, -3, 6, 6)
            
            painter.restore()
        
        # Connecting rod
        rod_y = 18 + math.sin(self.wheel_rotation) * 6
        painter.setBrush(QBrush(QColor(120, 120, 125)))
        painter.setPen(QPen(QColor(80, 85, 90), 1.0))
        painter.drawRoundedRect(-35, int(rod_y) - 2, 50, 4, 2, 2)
        
        # Piston rod
        piston_x = 25 + math.cos(self.wheel_rotation) * 5
        painter.drawRect(int(piston_x), 14, 12, 3)
        
        # Headlight
        if self.headlight_on:
            # Light glow
            light_glow = QRadialGradient(38, -5, 20)
            light_glow.setColorAt(0.0, QColor(255, 255, 200, 180))
            light_glow.setColorAt(0.5, QColor(255, 255, 150, 80))
            light_glow.setColorAt(1.0, QColor(255, 255, 100, 0))
            
            painter.setBrush(QBrush(light_glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(18, -25, 40, 40)
            
            # Light beam
            beam_gradient = QLinearGradient(38, -5, 80, 0)
            beam_gradient.setColorAt(0.0, QColor(255, 255, 200, 60))
            beam_gradient.setColorAt(1.0, QColor(255, 255, 200, 0))
            
            beam_path = QPainterPath()
            beam_path.moveTo(38, -8)
            beam_path.lineTo(100, -20)
            beam_path.lineTo(100, 15)
            beam_path.lineTo(38, -2)
            beam_path.closeSubpath()
            
            painter.fillPath(beam_path, QBrush(beam_gradient))
        
        # Headlight housing
        painter.setBrush(QBrush(QColor(200, 200, 210)))
        painter.setPen(QPen(QColor(100, 105, 110), 1.0))
        painter.drawEllipse(32, -11, 12, 12)
        
        # Light lens
        lens_gradient = QRadialGradient(38, -5, 5)
        lens_gradient.setColorAt(0.0, QColor(255, 255, 220))
        lens_gradient.setColorAt(1.0, QColor(255, 255, 180))
        
        painter.setBrush(QBrush(lens_gradient))
        painter.drawEllipse(34, -9, 8, 8)
        
        # Whistle
        painter.setBrush(QBrush(QColor(180, 160, 70)))
        painter.setPen(QPen(QColor(120, 105, 50), 1.0))
        painter.drawRect(-25, -30, 6, 15)
        painter.drawEllipse(-27, -33, 10, 6)
        
        # Bell
        painter.setBrush(QBrush(QColor(200, 180, 90)))
        painter.setPen(QPen(QColor(140, 125, 60), 1.0))
        painter.drawEllipse(-10, -25, 10, 8)
        
        painter.restore()
