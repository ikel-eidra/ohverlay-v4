"""
Colorful Toy Steam Locomotive v3.0 - Desktop Train
Runs along bottom taskbar edge (not top)
Compact, colorful design like old toy trains
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
class SteamParticle:
    """Steam/smoke from chimney"""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    life: float = 1.0
    alpha: int = 200
    
    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.size += dt * 8
        self.life -= dt * 0.35
        self.alpha = int(200 * self.life)


class DesktopTrain(QWidget):
    """
    Colorful toy steam locomotive - compact design
    Runs along BOTTOM taskbar edge (not top!)
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
        
        # Screen dimensions
        self.screen_width = 3840
        self.taskbar_top = 1040  # Top of taskbar (bottom of usable screen)
        self.track_y = self.taskbar_top - 35  # Run JUST ABOVE taskbar
        
        # Position - start from left, at BOTTOM
        self.x = -100.0
        self.y = self.track_y
        
        # Movement - horizontal only
        self.speed = 100.0  # Pixels per second
        self.direction = 1  # 1 = right, -1 = left
        
        # Animation
        self.time = 0.0
        self.wheel_rotation = 0.0
        self.chuff_timer = 0.0
        
        # Steam particles
        self.steam_particles: List[SteamParticle] = []
        
        # **COLORFUL TOY TRAIN COLORS**
        self.colors = {
            'body': QColor(220, 50, 50),      # Bright RED
            'body_highlight': QColor(255, 100, 100),
            'body_shadow': QColor(180, 30, 30),
            'boiler': QColor(50, 120, 200),    # Bright BLUE
            'boiler_highlight': QColor(100, 170, 255),
            'chimney': QColor(255, 200, 50),   # YELLOW
            'gold': QColor(255, 215, 0),       # GOLD
            'black': QColor(40, 40, 40),       # Black details
            'wheel': QColor(80, 80, 80),       # Grey wheels
            'white': QColor(240, 240, 240),    # White details
        }
        
        # Smaller compact size
        self.scale = 0.5
        
        self.resize(120, 70)
        self.move(int(self.x), int(self.y - 35))
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update train - runs horizontally on bottom track"""
        self.time += dt
        
        # Simple horizontal movement
        self.x += self.speed * self.direction * dt
        
        # Wrap around screen
        if self.direction == 1 and self.x > self.screen_width + 50:
            self.x = -80
        elif self.direction == -1 and self.x < -80:
            self.x = self.screen_width + 50
        
        # Keep at track level
        self.y = self.track_y
        
        # Update wheel rotation
        self.wheel_rotation += (self.speed * dt * 0.8)
        
        # Generate steam
        self.chuff_timer += dt
        if self.chuff_timer > 0.25:
            self.chuff_timer = 0.0
            self._emit_steam()
        
        # Update steam
        for particle in self.steam_particles[:]:
            particle.update(dt)
            if particle.life <= 0:
                self.steam_particles.remove(particle)
        
        self.move(int(self.x - 60), int(self.y - 35))
        self.update()
    
    def _emit_steam(self):
        """Emit steam puffs from chimney"""
        # Chimney position (relative to train center)
        chimney_x = self.x + 15
        chimney_y = self.y - 25
        
        for _ in range(4):
            self.steam_particles.append(SteamParticle(
                x=chimney_x + random.uniform(-3, 3),
                y=chimney_y,
                vx=random.uniform(-20, -40) if self.direction == 1 else random.uniform(20, 40),
                vy=random.uniform(-60, -100),
                size=random.uniform(4, 8)
            ))
    
    def paintEvent(self, event):
        """Render colorful toy train"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        cx = 60
        cy = 35
        
        painter.save()
        painter.translate(cx, cy)
        painter.scale(self.scale, self.scale)
        
        # Draw steam behind train
        self._draw_steam(painter)
        
        # Draw colorful train
        self._draw_train_body(painter)
        
        painter.restore()
    
    def _draw_steam(self, painter: QPainter):
        """Draw steam puffs"""
        for particle in self.steam_particles:
            px = particle.x - self.x + 60
            py = particle.y - self.y + 35
            
            if not (0 <= px <= 120 and -50 <= py <= 70):
                continue
            
            gradient = QRadialGradient(px, py, particle.size)
            gradient.setColorAt(0.0, QColor(255, 255, 255, particle.alpha))
            gradient.setColorAt(1.0, QColor(240, 248, 255, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(px - particle.size), 
                int(py - particle.size),
                int(particle.size * 2), 
                int(particle.size * 2)
            )
    
    def _draw_train_body(self, painter: QPainter):
        """Draw colorful compact train"""
        c = self.colors
        
        # === CHIMNEY (Yellow) ===
        chimney_grad = QLinearGradient(12, -35, 18, -15)
        chimney_grad.setColorAt(0.0, c['chimney'].lighter(120))
        chimney_grad.setColorAt(1.0, c['chimney'].darker(110))
        
        painter.setBrush(QBrush(chimney_grad))
        painter.setPen(QPen(c['black'], 1))
        
        # Chimney base
        painter.drawRect(10, -15, 12, 8)
        # Chimney stack
        painter.drawRect(12, -35, 8, 22)
        # Chimney top (gold rim)
        painter.setBrush(QBrush(c['gold']))
        painter.drawEllipse(10, -38, 12, 6)
        
        # === BOILER (Blue) ===
        boiler_grad = QLinearGradient(0, -12, 0, 12)
        boiler_grad.setColorAt(0.0, c['boiler_highlight'])
        boiler_grad.setColorAt(0.5, c['boiler'])
        boiler_grad.setColorAt(1.0, c['boiler'].darker(120))
        
        painter.setBrush(QBrush(boiler_grad))
        painter.setPen(QPen(c['black'], 1.5))
        
        # Main boiler (rounded cylinder)
        painter.drawRoundedRect(-35, -12, 55, 24, 8, 8)
        
        # Gold bands on boiler
        painter.setPen(QPen(c['gold'], 2))
        painter.drawLine(-30, -12, -30, 12)
        painter.drawLine(0, -12, 0, 12)
        painter.drawLine(15, -12, 15, 12)
        
        # === CAB (Red) ===
        cab_grad = QLinearGradient(-55, -15, -55, 20)
        cab_grad.setColorAt(0.0, c['body_highlight'])
        cab_grad.setColorAt(0.5, c['body'])
        cab_grad.setColorAt(1.0, c['body_shadow'])
        
        painter.setBrush(QBrush(cab_grad))
        painter.setPen(QPen(c['black'], 1.5))
        
        # Cab box
        painter.drawRect(-60, -15, 28, 35)
        
        # Cab roof
        roof_grad = QLinearGradient(-62, -20, -62, -15)
        roof_grad.setColorAt(0.0, c['black'].lighter(150))
        roof_grad.setColorAt(1.0, c['black'])
        painter.setBrush(QBrush(roof_grad))
        painter.drawRoundedRect(-62, -20, 32, 7, 3, 3)
        
        # Window (white with blue)
        painter.setBrush(QBrush(QColor(200, 230, 255)))
        painter.setPen(QPen(c['black'], 1))
        painter.drawRect(-57, -10, 15, 12)
        # Window frame
        painter.setPen(QPen(c['white'], 1))
        painter.drawLine(-50, -10, -50, 2)
        painter.drawLine(-57, -4, -42, -4)
        
        # === COWCATCHER (Front) ===
        painter.setBrush(QBrush(c['black'].lighter(120)))
        painter.setPen(QPen(c['black'], 1))
        
        cowcatcher = QPainterPath()
        cowcatcher.moveTo(22, -10)
        cowcatcher.lineTo(35, 0)
        cowcatcher.lineTo(22, 10)
        cowcatcher.lineTo(20, 10)
        cowcatcher.lineTo(20, -10)
        cowcatcher.closeSubpath()
        painter.drawPath(cowcatcher)
        
        # Gold bars on cowcatcher
        painter.setPen(QPen(c['gold'], 1.5))
        for i in range(3):
            y = -6 + i * 6
            painter.drawLine(22, int(y), 30, 0)
        
        # === BIG WHEELS (Colorful) ===
        wheel_positions = [(-40, 18), (-15, 18), (10, 18)]
        
        for wx, wy in wheel_positions:
            painter.save()
            painter.translate(wx, wy)
            painter.rotate(math.degrees(self.wheel_rotation))
            
            # Tire (black with red rim)
            tire_grad = QRadialGradient(0, 0, 10)
            tire_grad.setColorAt(0.7, c['wheel'])
            tire_grad.setColorAt(0.9, c['body'])  # Red rim
            tire_grad.setColorAt(1.0, c['black'])
            
            painter.setBrush(QBrush(tire_grad))
            painter.setPen(QPen(c['black'], 1.5))
            painter.drawEllipse(-10, -10, 20, 20)
            
            # Spokes (gold)
            painter.setPen(QPen(c['gold'], 2))
            for i in range(4):
                angle = i * math.pi / 2
                sx = math.cos(angle) * 7
                sy = math.sin(angle) * 7
                painter.drawLine(0, 0, int(sx), int(sy))
            
            # Center hub (gold)
            painter.setBrush(QBrush(c['gold']))
            painter.setPen(QPen(c['black'], 1))
            painter.drawEllipse(-3, -3, 6, 6)
            
            painter.restore()
        
        # Connecting rod
        rod_y = 18 + math.sin(self.wheel_rotation) * 4
        painter.setBrush(QBrush(c['white'].darker(120)))
        painter.setPen(QPen(c['black'], 1))
        painter.drawRoundedRect(-40, int(rod_y) - 2, 50, 4, 2, 2)
        
        # === HEADLIGHT (White glow) ===
        light_x = 20
        light_y = -5
        
        # Glow
        glow = QRadialGradient(light_x, light_y, 15)
        glow.setColorAt(0.0, QColor(255, 255, 200, 150))
        glow.setColorAt(1.0, QColor(255, 255, 100, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(light_x - 15), int(light_y - 15), 30, 30)
        
        # Light housing
        painter.setBrush(QBrush(c['white']))
        painter.setPen(QPen(c['black'], 1))
        painter.drawEllipse(int(light_x - 5), int(light_y - 5), 10, 10)
        
        # Lens
        lens_grad = QRadialGradient(light_x - 2, light_y - 2, 3)
        lens_grad.setColorAt(0.0, QColor(255, 255, 220))
        lens_grad.setColorAt(1.0, QColor(255, 255, 180))
        painter.setBrush(QBrush(lens_grad))
        painter.drawEllipse(int(light_x - 3), int(light_y - 3), 6, 6)
        
        # === WHISTLE (Gold) ===
        painter.setBrush(QBrush(c['gold']))
        painter.setPen(QPen(c['black'], 1))
        painter.drawRect(-25, -28, 5, 10)
        painter.drawEllipse(-27, -32, 9, 6)
        
        # === BELL (Gold) ===
        painter.setBrush(QBrush(c['gold'].lighter(110)))
        painter.drawEllipse(-10, -25, 8, 8)
