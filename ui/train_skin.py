"""
1800s Steam Locomotive v4.0 - Realistic Vintage Train
Authentic 19th century design - black with brass accents
Runs along bottom taskbar edge
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
    """Thick black/brown steam from chimney"""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    life: float = 1.0
    gray: int = 180
    
    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.size += dt * 10
        self.life -= dt * 0.3
        self.gray = min(220, self.gray + int(dt * 20))


class DesktopTrain(QWidget):
    """
    Authentic 1800s steam locomotive
    Black iron body, brass fittings, realistic proportions
    Runs on BOTTOM taskbar edge
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
        
        # Screen - run on BOTTOM (taskbar edge)
        self.screen_width = 3840
        # For 1080p screen: taskbar at ~1040, run at ~1000 (just above)
        self.track_y = 1000  
        
        # Position
        self.x = -80.0
        self.y = self.track_y
        
        # Movement
        self.speed = 80.0
        self.direction = 1
        
        # Animation
        self.time = 0.0
        self.wheel_rotation = 0.0
        self.piston_phase = 0.0
        self.chuff_timer = 0.0
        
        # Steam
        self.steam_particles: List[SteamParticle] = []
        
        # **1800s AUTHENTIC COLORS**
        self.colors = {
            'body_black': QColor(25, 25, 28),       # Sooty black
            'body_dark': QColor(35, 35, 38),        # Dark iron
            'boiler': QColor(40, 40, 43),           # Boiler black
            'brass': QColor(184, 134, 11),          # Antique brass
            'brass_dark': QColor(140, 100, 8),      # Dark brass
            'copper': QColor(165, 105, 60),         # Aged copper
            'rust': QColor(120, 60, 30, 100),       # Rust spots
            'white': QColor(240, 240, 240),         # Steam
            'smoke': QColor(80, 80, 85),            # Dark smoke
        }
        
        # Size
        self.scale = 0.55
        
        self.resize(140, 80)
        self.move(int(self.x - 70), int(self.y - 40))
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update 1800s locomotive"""
        self.time += dt
        
        # Move horizontally on bottom
        self.x += self.speed * self.direction * dt
        
        # Wrap
        if self.direction == 1 and self.x > self.screen_width + 60:
            self.x = -60
        elif self.direction == -1 and self.x < -60:
            self.x = self.screen_width + 60
        
        self.y = self.track_y
        
        # Animation
        self.wheel_rotation += self.speed * dt * 0.6
        self.piston_phase += self.speed * dt * 0.6
        
        # Steam (chuff chuff)
        self.chuff_timer += dt
        if self.chuff_timer > 0.35:
            self.chuff_timer = 0.0
            self._emit_steam()
        
        # Update steam
        for particle in self.steam_particles[:]:
            particle.update(dt)
            if particle.life <= 0:
                self.steam_particles.remove(particle)
        
        self.move(int(self.x - 70), int(self.y - 40))
        self.update()
    
    def _emit_steam(self):
        """Thick 1800s style steam"""
        chimney_x = self.x + (18 if self.direction == 1 else -18)
        chimney_y = self.y - 30
        
        for _ in range(5):
            self.steam_particles.append(SteamParticle(
                x=chimney_x + random.uniform(-3, 3),
                y=chimney_y,
                vx=random.uniform(-25, -50) if self.direction == 1 else random.uniform(25, 50),
                vy=random.uniform(-70, -110),
                size=random.uniform(6, 12),
                gray=random.randint(150, 200)
            ))
    
    def paintEvent(self, event):
        """Render 1800s locomotive"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        cx = 70
        cy = 40
        
        painter.save()
        painter.translate(cx, cy)
        painter.scale(self.scale, self.scale)
        
        # Flip if going left
        if self.direction == -1:
            painter.scale(-1, 1)
        
        # Draw steam behind
        self._draw_steam(painter)
        
        # Draw locomotive
        self._draw_locomotive(painter)
        
        painter.restore()
    
    def _draw_steam(self, painter: QPainter):
        """Draw thick industrial steam"""
        for particle in self.steam_particles:
            px = particle.x - self.x + 70
            py = particle.y - self.y + 40
            
            if not (0 <= px <= 140 and -60 <= py <= 80):
                continue
            
            # Dark smoke for 1800s coal burning
            gray = particle.gray
            alpha = int(120 * particle.life)
            
            gradient = QRadialGradient(px, py, particle.size)
            gradient.setColorAt(0.0, QColor(gray, gray, gray, alpha))
            gradient.setColorAt(0.5, QColor(gray-20, gray-20, gray-20, int(alpha*0.5)))
            gradient.setColorAt(1.0, QColor(gray-40, gray-40, gray-40, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(px - particle.size),
                int(py - particle.size),
                int(particle.size * 2),
                int(particle.size * 2)
            )
    
    def _draw_locomotive(self, painter: QPainter):
        """Draw authentic 1800s steam locomotive"""
        c = self.colors
        
        # === DOMED FIREBOX (rear section) ===
        # 1800s locomotives had distinctive domed firebox
        firebox_grad = QRadialGradient(-50, -5, 25)
        firebox_grad.setColorAt(0.0, c['body_dark'].lighter(110))
        firebox_grad.setColorAt(0.5, c['body_black'])
        firebox_grad.setColorAt(1.0, c['body_dark'].darker(120))
        
        painter.setBrush(QBrush(firebox_grad))
        painter.setPen(QPen(c['body_dark'].darker(150), 1.5))
        
        # Firebox body
        painter.drawRoundedRect(-70, -15, 35, 30, 8, 8)
        
        # Firebox dome
        painter.setBrush(QBrush(c['body_black'].lighter(105)))
        painter.drawEllipse(-65, -28, 25, 18)
        
        # Brass dome top
        painter.setBrush(QBrush(c['brass']))
        painter.drawEllipse(-62, -32, 19, 8)
        
        # === BOILER (main cylinder) ===
        boiler_grad = QLinearGradient(0, -12, 0, 12)
        boiler_grad.setColorAt(0.0, c['boiler'].lighter(115))
        boiler_grad.setColorAt(0.3, c['boiler'])
        boiler_grad.setColorAt(0.7, c['boiler'])
        boiler_grad.setColorAt(1.0, c['boiler'].darker(130))
        
        painter.setBrush(QBrush(boiler_grad))
        painter.setPen(QPen(c['body_dark'].darker(150), 2))
        
        # Main boiler (long cylinder)
        boiler_path = QPainterPath()
        boiler_path.moveTo(-38, -12)
        boiler_path.cubicTo(-20, -14, 25, -14, 45, -10)
        boiler_path.lineTo(45, 10)
        boiler_path.cubicTo(25, 14, -20, 14, -38, 12)
        boiler_path.closeSubpath()
        painter.drawPath(boiler_path)
        
        # Brass bands on boiler (riveted look)
        painter.setPen(QPen(c['brass'], 2.5))
        for x in [-20, 0, 20]:
            painter.drawLine(x, -13, x, 13)
        
        # Rivets on bands
        painter.setBrush(QBrush(c['brass_dark']))
        painter.setPen(Qt.PenStyle.NoPen)
        for x in [-20, 0, 20]:
            for y in [-10, -5, 0, 5, 10]:
                painter.drawEllipse(int(x-1.5), int(y-1.5), 3, 3)
        
        # === CHIMNEY/SMOKESTACK (tall 1800s style) ===
        chimney_grad = QLinearGradient(35, -40, 40, -10)
        chimney_grad.setColorAt(0.0, c['copper'].lighter(120))
        chimney_grad.setColorAt(0.5, c['copper'])
        chimney_grad.setColorAt(1.0, c['copper'].darker(120))
        
        painter.setBrush(QBrush(chimney_grad))
        painter.setPen(QPen(c['body_dark'], 1))
        
        # Chimney base (wide)
        painter.drawRect(32, -12, 10, 8)
        # Chimney stack (tapered)
        chimney = QPainterPath()
        chimney.moveTo(34, -12)
        chimney.lineTo(40, -12)
        chimney.lineTo(42, -45)
        chimney.lineTo(32, -45)
        chimney.closeSubpath()
        painter.drawPath(chimney)
        
        # Chimney cap (brass)
        painter.setBrush(QBrush(c['brass']))
        painter.drawEllipse(30, -48, 14, 6)
        
        # === COWL CATCHER/PILOT (front) ===
        painter.setBrush(QBrush(c['body_dark']))
        painter.setPen(QPen(c['body_dark'].darker(150), 1))
        
        cowcatcher = QPainterPath()
        cowcatcher.moveTo(45, -12)
        cowcatcher.lineTo(60, 0)
        cowcatcher.lineTo(45, 12)
        cowcatcher.lineTo(42, 12)
        cowcatcher.lineTo(42, -12)
        cowcatcher.closeSubpath()
        painter.drawPath(cowcatcher)
        
        # Cowcatcher bars (wood/metal)
        painter.setPen(QPen(c['copper'], 2))
        for i in range(4):
            y = -8 + i * 5
            painter.drawLine(44, int(y), 55, 0)
        
        # === LARGE DRIVING WHEELS (1800s style) ===
        # Three big wheels - signature of steam locomotives
        wheel_centers = [(-45, 18), (-15, 18), (15, 18)]
        
        for wx, wy in wheel_centers:
            painter.save()
            painter.translate(wx, wy)
            painter.rotate(math.degrees(self.wheel_rotation))
            
            # Wheel tire (iron with red trim - 1800s style)
            tire_grad = QRadialGradient(0, 0, 12)
            tire_grad.setColorAt(0.7, c['body_dark'])
            tire_grad.setColorAt(0.85, QColor(100, 30, 30))  # Red trim
            tire_grad.setColorAt(1.0, c['body_black'])
            
            painter.setBrush(QBrush(tire_grad))
            painter.setPen(QPen(c['body_dark'], 1.5))
            painter.drawEllipse(-12, -12, 24, 24)
            
            # Spokes (heavy iron)
            painter.setPen(QPen(c['body_dark'].lighter(120), 3))
            for i in range(6):
                angle = i * math.pi / 3
                sx = math.cos(angle) * 9
                sy = math.sin(angle) * 9
                painter.drawLine(0, 0, int(sx), int(sy))
            
            # Center hub (brass axle box)
            hub_grad = QRadialGradient(0, 0, 5)
            hub_grad.setColorAt(0.0, c['brass'].lighter(130))
            hub_grad.setColorAt(1.0, c['brass_dark'])
            painter.setBrush(QBrush(hub_grad))
            painter.setPen(QPen(c['brass_dark'], 1))
            painter.drawEllipse(-4, -4, 8, 8)
            
            painter.restore()
        
        # === SIDE RODS (connecting wheels) ===
        rod_offset = math.sin(self.piston_phase) * 5
        
        painter.setBrush(QBrush(c['body_dark'].lighter(80)))
        painter.setPen(QPen(c['body_dark'], 1))
        
        # Main rod
        painter.drawRoundedRect(-48, int(18 + rod_offset) - 2, 65, 4, 2, 2)
        
        # Rod bolts (brass)
        painter.setBrush(QBrush(c['brass']))
        for wx, wy in wheel_centers:
            painter.drawEllipse(int(wx - 3), int(18 + rod_offset - 3), 6, 6)
        
        # === HEADLAMP (1800s oil lamp style) ===
        lamp_x = 38
        lamp_y = -8
        
        # Lamp glow
        glow = QRadialGradient(lamp_x, lamp_y, 18)
        glow.setColorAt(0.0, QColor(255, 255, 200, 100))
        glow.setColorAt(0.5, QColor(255, 240, 150, 50))
        glow.setColorAt(1.0, QColor(255, 200, 100, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(lamp_x - 18), int(lamp_y - 18), 36, 36)
        
        # Lamp housing (brass)
        painter.setBrush(QBrush(c['brass']))
        painter.setPen(QPen(c['brass_dark'], 1))
        painter.drawEllipse(int(lamp_x - 6), int(lamp_y - 6), 12, 12)
        
        # Lamp lens
        lens_grad = QRadialGradient(lamp_x - 2, lamp_y - 2, 4)
        lens_grad.setColorAt(0.0, QColor(255, 255, 240))
        lens_grad.setColorAt(1.0, QColor(255, 255, 200))
        painter.setBrush(QBrush(lens_grad))
        painter.drawEllipse(int(lamp_x - 4), int(lamp_y - 4), 8, 8)
        
        # === WHISTLE (brass steam whistle) ===
        painter.setBrush(QBrush(c['brass']))
        painter.setPen(QPen(c['brass_dark'], 1))
        painter.drawRect(-35, -35, 5, 12)
        painter.drawEllipse(-37, -39, 9, 6)
        
        # === BELL (brass warning bell) ===
        painter.setBrush(QBrush(c['brass'].lighter(110)))
        painter.setPen(QPen(c['brass_dark'], 1))
        painter.drawEllipse(-18, -32, 10, 10)
        # Bell mount
        painter.setBrush(QBrush(c['body_dark']))
        painter.drawRect(-16, -28, 4, 6)
        
        # === NUMBER PLATE (brass plate with black numbers) ===
        painter.setBrush(QBrush(c['brass']))
        painter.setPen(QPen(c['brass_dark'], 1))
        painter.drawRect(25, -5, 12, 8)
        # Number
        painter.setPen(QPen(c['body_black'], 1.5))
        font = painter.font()
        font.setPointSize(6)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(27, 2, "47")
        
        # === RUST SPOTS (weathering) ===
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(6):
            rx = random.uniform(-60, 40)
            ry = random.uniform(-10, 15)
            painter.setBrush(QBrush(c['rust']))
            painter.drawEllipse(int(rx), int(ry), 6, 4)
