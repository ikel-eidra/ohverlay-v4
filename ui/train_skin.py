"""
VINTAGE Steam Locomotive v2.0 - Non-Biological Object
Old-timey train with massive steam clouds, travels screen edges like tracks
"""

import math
import random
from typing import List, Tuple
from dataclasses import dataclass, field
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QPen, QBrush, QFont
)
from PySide6.QtWidgets import QWidget


@dataclass
class SteamParticle:
    """Big puffy steam from chimney"""
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
        self.vx *= 0.98  # Air resistance
        self.vy *= 0.95
        self.size += dt * 15  # Expand quickly
        self.life -= dt * 0.35
        self.alpha = int(200 * self.life)


class VintageSteamTrain(QWidget):
    """
    Old-timey steam locomotive with massive steam clouds
    Runs along screen edges like railway tracks
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
        
        # Track paths - runs along screen edges like railway
        # Top edge (y=40) and bottom edge (y=1040 for 1080p - taskbar)
        self.track_y_positions = [45, 1035]  # Top and bottom "tracks"
        self.current_track = 0  # 0 = top, 1 = bottom
        self.direction = 1  # 1 = right, -1 = left
        
        # Position - start at left side
        self.x = -150.0
        self.y = self.track_y_positions[0]
        
        # Movement
        self.speed = 120.0
        
        # Visual
        self.scale = 0.8
        self.wheel_rotation = 0.0
        self.drive_rod_phase = 0.0
        self.steam_particles: List[SteamParticle] = []
        self.chuff_timer = 0.0
        self.chuff_rate = 0.25  # Steam puff every 0.25 seconds
        
        # VINTAGE Colors - brass, copper, black
        self.black_color = QColor(25, 28, 32)  # Sooty black
        self.boiler_color = QColor(40, 42, 45)  # Dark boiler
        self.brass_color = QColor(218, 165, 32)  # Antique brass
        self.copper_color = QColor(184, 115, 51)  # Aged copper
        self.red_color = QColor(140, 35, 35)  # Deep cab red
        self.rust_color = QColor(160, 82, 45, 60)  # Rust patches
        
        # Headlight
        self.headlight_on = True
        self.headlight_pulse = 0.0
        
        # Whistle steam
        self.whistle_active = False
        self.whistle_timer = 0.0
        
        self.time = 0.0
        self.resize(200, 120)
        self.move(int(self.x), int(self.y - 60))
    
    def update_state(self, dt: float, target_x: float = None, target_y: float = None):
        """Update train position along edge tracks"""
        self.time += dt
        
        # Move horizontally
        self.x += self.speed * self.direction * dt
        
        # Switch tracks when reaching screen edges
        screen_width = 3840  # Dual monitor width
        
        if self.direction == 1 and self.x > screen_width + 100:
            # Reached right edge, switch to bottom track going left
            self.direction = -1
            self.current_track = 1
            self.x = screen_width + 100
            self._toot_whistle()
        elif self.direction == -1 and self.x < -200:
            # Reached left edge, switch to top track going right
            self.direction = 1
            self.current_track = 0
            self.x = -200
            self._toot_whistle()
        
        self.y = self.track_y_positions[self.current_track]
        
        # Update wheels and rods
        self.wheel_rotation += (self.speed * dt * 0.8)
        self.drive_rod_phase += (self.speed * dt * 0.8)
        
        # Generate steam (chuff chuff!)
        self.chuff_timer += dt
        if self.chuff_timer >= self.chuff_rate:
            self.chuff_timer = 0.0
            self._emit_steam_burst()
        
        # Whistle steam
        if self.whistle_active:
            self.whistle_timer -= dt
            if self.whistle_timer <= 0:
                self.whistle_active = False
            # Extra steam during whistle
            if random.random() < 0.3:
                self._emit_whistle_steam()
        
        # Update steam particles
        for particle in self.steam_particles[:]:
            particle.update(dt)
            if particle.life <= 0:
                self.steam_particles.remove(particle)
        
        # Headlight pulse
        self.headlight_pulse += dt * 4
        
        self.move(int(self.x - 100), int(self.y - 60))
        self.update()
    
    def _toot_whistle(self):
        """Toot toot! Train whistle"""
        self.whistle_active = True
        self.whistle_timer = 1.5
        # Burst of steam
        for _ in range(15):
            self._emit_whistle_steam()
    
    def _emit_steam_burst(self):
        """Emit big steam puff from chimney - CHUFF CHUFF!"""
        # Chimney position (above boiler)
        chimney_x = 20
        chimney_y = -35
        
        # Multiple particles for big puff
        for _ in range(8):
            # Steam goes up and slightly opposite to movement
            steam_vx = random.uniform(-30, 30) - (self.direction * 20)
            steam_vy = random.uniform(-80, -150)  # Upward
            
            particle = SteamParticle(
                x=self.x + chimney_x + random.uniform(-5, 5),
                y=self.y + chimney_y,
                vx=steam_vx,
                vy=steam_vy,
                size=random.uniform(15, 30)
            )
            self.steam_particles.append(particle)
    
    def _emit_whistle_steam(self):
        """Extra steam for whistle effect"""
        chimney_x = 20
        chimney_y = -35
        
        particle = SteamParticle(
            x=self.x + chimney_x + random.uniform(-3, 3),
            y=self.y + chimney_y - 10,
            vx=random.uniform(-40, 40),
            vy=random.uniform(-100, -180),
            size=random.uniform(20, 40)
        )
        self.steam_particles.append(particle)
    
    def paintEvent(self, event):
        """Render vintage steam train"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Draw steam behind train
        self._draw_steam(painter)
        
        # Draw the train
        self._draw_vintage_train(painter)
    
    def _draw_steam(self, painter: QPainter):
        """Draw massive white steam clouds"""
        for particle in self.steam_particles:
            px = particle.x - self.x + 100
            py = particle.y - self.y + 60
            
            # Skip if out of bounds
            if px < -50 or px > 250 or py < -50:
                continue
            
            # Big fluffy steam
            for i in range(3):  # Multiple overlapping circles for fluffiness
                offset_x = math.sin(particle.life * 5 + i) * particle.size * 0.3
                offset_y = math.cos(particle.life * 3 + i) * particle.size * 0.2
                
                size_var = particle.size * (1 + i * 0.2)
                alpha = int(particle.alpha * (1 - i * 0.2))
                
                steam_gradient = QRadialGradient(
                    px + offset_x, py + offset_y, size_var
                )
                steam_gradient.setColorAt(0.0, QColor(255, 255, 255, alpha))
                steam_gradient.setColorAt(0.4, QColor(240, 248, 255, int(alpha * 0.7)))
                steam_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
                
                painter.setBrush(QBrush(steam_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(
                    int(px + offset_x - size_var), 
                    int(py + offset_y - size_var),
                    int(size_var * 2), 
                    int(size_var * 2)
                )
    
    def _draw_vintage_train(self, painter: QPainter):
        """Draw old-timey steam locomotive"""
        cx = 100
        cy = 60
        
        painter.save()
        painter.translate(cx, cy)
        painter.scale(self.scale, self.scale)
        
        # Shadow on the "track"
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(-90, 28, 180, 15, 7, 7)
        
        # === BOILER (main cylinder) ===
        # Metallic gradient for old boiler
        boiler_gradient = QLinearGradient(-40, -20, 40, 20)
        boiler_gradient.setColorAt(0.0, self.boiler_color.darker(130))
        boiler_gradient.setColorAt(0.2, self.boiler_color)
        boiler_gradient.setColorAt(0.5, self.boiler_color.lighter(120))
        boiler_gradient.setColorAt(0.8, self.boiler_color)
        boiler_gradient.setColorAt(1.0, self.boiler_color.darker(140))
        
        painter.setBrush(QBrush(boiler_gradient))
        painter.setPen(QPen(QColor(15, 18, 22), 2.0))
        
        # Main boiler shape
        boiler_path = QPainterPath()
        boiler_path.moveTo(55, -18)
        boiler_path.cubicTo(65, -15, 65, 15, 55, 18)  # Front curve (smokebox)
        boiler_path.lineTo(-50, 20)  # Bottom
        boiler_path.cubicTo(-60, 18, -60, -18, -50, -20)  # Rear curve
        boiler_path.closeSubpath()
        painter.drawPath(boiler_path)
        
        # Brass bands around boiler
        painter.setPen(QPen(self.brass_color, 3.0))
        painter.drawLine(-35, -20, -35, 20)
        painter.drawLine(-5, -20, -5, 20)
        painter.drawLine(30, -18, 30, 18)
        
        # === SMOKEBOX (front section) ===
        smokebox_gradient = QLinearGradient(30, -18, 65, 18)
        smokebox_gradient.setColorAt(0.0, self.black_color.lighter(110))
        smokebox_gradient.setColorAt(1.0, self.black_color)
        
        painter.setBrush(QBrush(smokebox_gradient))
        painter.setPen(QPen(QColor(10, 12, 15), 2.0))
        painter.drawRoundedRect(30, -18, 35, 36, 5, 5)
        
        # Smokebox door
        door_gradient = QRadialGradient(55, 0, 12)
        door_gradient.setColorAt(0.0, self.black_color.lighter(150))
        door_gradient.setColorAt(1.0, self.black_color)
        painter.setBrush(QBrush(door_gradient))
        painter.drawEllipse(48, -10, 20, 20)
        
        # === CHIMNEY/SMOKESTACK (tall vintage style) ===
        chimney_x = 20
        chimney_base = -20
        
        # Chimney shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
        painter.drawRect(chimney_x - 8, chimney_base - 50, 16, 52)
        
        # Chimney stack (tapered)
        chimney_gradient = QLinearGradient(chimney_x, chimney_base - 55, chimney_x + 10, chimney_base)
        chimney_gradient.setColorAt(0.0, self.black_color.lighter(140))
        chimney_gradient.setColorAt(0.5, self.boiler_color)
        chimney_gradient.setColorAt(1.0, self.black_color)
        
        painter.setBrush(QBrush(chimney_gradient))
        painter.setPen(QPen(QColor(15, 18, 22), 1.5))
        
        # Chimney shape (tall vintage)
        chimney_path = QPainterPath()
        chimney_path.moveTo(chimney_x - 6, chimney_base)
        chimney_path.lineTo(chimney_x - 4, chimney_base - 45)
        chimney_path.lineTo(chimney_x - 10, chimney_base - 50)
        chimney_path.lineTo(chimney_x - 10, chimney_base - 58)
        chimney_path.lineTo(chimney_x + 10, chimney_base - 58)  # Wide top
        chimney_path.lineTo(chimney_x + 10, chimney_base - 50)
        chimney_path.lineTo(chimney_x + 4, chimney_base - 45)
        chimney_path.lineTo(chimney_x + 6, chimney_base)
        chimney_path.closeSubpath()
        painter.drawPath(chimney_path)
        
        # Brass chimney cap
        painter.setBrush(QBrush(self.brass_color))
        painter.setPen(QPen(self.copper_color, 1.0))
        painter.drawRoundedRect(chimney_x - 11, chimney_base - 60, 22, 6, 2, 2)
        
        # === SAND DOME (classic feature) ===
        dome_gradient = QRadialGradient(-10, -25, 15)
        dome_gradient.setColorAt(0.0, self.boiler_color.lighter(130))
        dome_gradient.setColorAt(1.0, self.boiler_color)
        painter.setBrush(QBrush(dome_gradient))
        painter.setPen(QPen(QColor(15, 18, 22), 1.5))
        painter.drawEllipse(-20, -35, 20, 18)
        
        # === CAB (rear section) ===
        cab_gradient = QLinearGradient(-70, -30, -60, 30)
        cab_gradient.setColorAt(0.0, self.red_color.lighter(110))
        cab_gradient.setColorAt(0.4, self.red_color)
        cab_gradient.setColorAt(1.0, self.red_color.darker(130))
        
        painter.setBrush(QBrush(cab_gradient))
        painter.setPen(QPen(QColor(80, 25, 25), 2.0))
        
        # Cab box
        painter.drawRect(-75, -28, 28, 56)
        
        # Cab roof (curved vintage style)
        roof_gradient = QLinearGradient(-75, -38, -75, -28)
        roof_gradient.setColorAt(0.0, self.black_color.lighter(150))
        roof_gradient.setColorAt(1.0, self.black_color)
        painter.setBrush(QBrush(roof_gradient))
        painter.setPen(QPen(QColor(15, 18, 22), 1.5))
        
        roof_path = QPainterPath()
        roof_path.moveTo(-78, -28)
        roof_path.quadTo(-61, -42, -44, -28)
        painter.drawPath(roof_path)
        painter.drawLine(-78, -28, -44, -28)
        
        # Cab window
        window_gradient = QLinearGradient(-68, -20, -60, -5)
        window_gradient.setColorAt(0.0, QColor(200, 220, 240))
        window_gradient.setColorAt(1.0, QColor(150, 170, 190))
        painter.setBrush(QBrush(window_gradient))
        painter.setPen(QPen(QColor(60, 70, 80), 2.0))
        painter.drawRect(-72, -22, 18, 18)
        
        # Window frame
        painter.setPen(QPen(QColor(40, 50, 60), 1.0))
        painter.drawLine(-63, -22, -63, -4)
        painter.drawLine(-72, -13, -54, -13)
        
        # Window shine
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
        painter.drawLine(-70, -20, -66, -10)
        
        # === COWCATCHER (pilot) - Old style ===
        painter.setBrush(QBrush(QColor(60, 60, 65)))
        painter.setPen(QPen(QColor(30, 35, 40), 1.5))
        
        cowcatcher = QPainterPath()
        cowcatcher.moveTo(65, -15)
        cowcatcher.lineTo(85, 0)
        cowcatcher.lineTo(65, 15)
        cowcatcher.lineTo(60, 15)
        cowcatcher.lineTo(60, -15)
        cowcatcher.closeSubpath()
        painter.drawPath(cowcatcher)
        
        # Cowcatcher bars (wood beam style)
        painter.setPen(QPen(self.brass_color, 2.5))
        for i in range(4):
            y_pos = -10 + i * 7
            painter.drawLine(62, int(y_pos), 78, 0)
        
        # === BIG DRIVING WHEELS (vintage style) ===
        wheel_centers = [(-45, 22), (-15, 22), (15, 22)]
        wheel_radius = 18
        
        for i, (wx, wy) in enumerate(wheel_centers):
            painter.save()
            painter.translate(wx, wy)
            painter.rotate(math.degrees(self.wheel_rotation) + i * 15)
            
            # Wheel tire (outer rim)
            tire_gradient = QRadialGradient(0, 0, wheel_radius)
            tire_gradient.setColorAt(0.7, QColor(50, 55, 60))
            tire_gradient.setColorAt(0.9, self.black_color)
            tire_gradient.setColorAt(1.0, QColor(30, 35, 40))
            
            painter.setBrush(QBrush(tire_gradient))
            painter.setPen(QPen(QColor(20, 25, 30), 2.0))
            painter.drawEllipse(-wheel_radius, -wheel_radius, 
                              wheel_radius * 2, wheel_radius * 2)
            
            # Spokes (thick vintage style)
            spoke_color = QColor(80, 85, 90)
            painter.setPen(QPen(spoke_color, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.Round))
            
            for j in range(8):
                angle = j * math.pi / 4
                sx = math.cos(angle) * (wheel_radius - 3)
                sy = math.sin(angle) * (wheel_radius - 3)
                painter.drawLine(0, 0, int(sx), int(sy))
            
            # Counterweight (classic steam loco feature)
            painter.setBrush(QBrush(QColor(70, 75, 80)))
            painter.setPen(QPen(QColor(40, 45, 50), 1.0))
            counter_path = QPainterPath()
            counter_path.moveTo(0, 0)
            counter_path.arcTo(-12, -12, 24, 24, -45, 90)
            counter_path.closeSubpath()
            painter.drawPath(counter_path)
            
            # Center hub (brass)
            hub_gradient = QRadialGradient(0, 0, 6)
            hub_gradient.setColorAt(0.0, self.brass_color.lighter(150))
            hub_gradient.setColorAt(1.0, self.brass_color.darker(120))
            painter.setBrush(QBrush(hub_gradient))
            painter.setPen(QPen(self.copper_color, 1.0))
            painter.drawEllipse(-5, -5, 10, 10)
            
            # Hub bolt
            painter.setBrush(QBrush(QColor(40, 45, 50)))
            painter.drawEllipse(-2, -2, 4, 4)
            
            painter.restore()
        
        # === DRIVE RODS (connecting the wheels) ===
        rod_y_offset = math.sin(math.radians(self.drive_rod_phase)) * 8
        
        # Main side rod
        painter.setBrush(QBrush(QColor(180, 185, 190)))
        painter.setPen(QPen(QColor(100, 105, 110), 1.5))
        
        rod_path = QPainterPath()
        rod_path.moveTo(-45 + 8, 22 + rod_y_offset)
        rod_path.lineTo(15 + 8, 22 + rod_y_offset)
        rod_path.lineTo(15 + 12, 22 + rod_y_offset + 5)
        rod_path.lineTo(-45 + 12, 22 + rod_y_offset + 5)
        rod_path.closeSubpath()
        painter.drawPath(rod_path)
        
        # Rod bolts (brass)
        for wx, wy in wheel_centers:
            painter.setBrush(QBrush(self.brass_color))
            painter.setPen(QPen(self.copper_color, 1.0))
            bolt_y = 22 + rod_y_offset + 2.5
            painter.drawEllipse(int(wx + 8 - 3), int(bolt_y - 3), 6, 6)
        
        # === PISTON ROD ===
        piston_x = 35 + math.cos(math.radians(self.drive_rod_phase)) * 6
        painter.setBrush(QBrush(QColor(160, 165, 170)))
        painter.setPen(QPen(QColor(90, 95, 100), 1.0))
        painter.drawRect(int(piston_x), 18, 20, 8)
        
        # Piston cylinder
        painter.setBrush(QBrush(QColor(60, 65, 70)))
        painter.setPen(QPen(QColor(30, 35, 40), 1.5))
        painter.drawRoundedRect(25, 15, 30, 14, 3, 3)
        
        # === HEADLIGHT (old brass style) ===
        light_x = 50
        light_y = -22
        
        # Light glow
        if self.headlight_on:
            pulse = 0.8 + 0.2 * math.sin(self.headlight_pulse)
            light_alpha = int(150 * pulse)
            
            glow = QRadialGradient(light_x, light_y, 35)
            glow.setColorAt(0.0, QColor(255, 255, 200, light_alpha))
            glow.setColorAt(0.3, QColor(255, 240, 150, int(light_alpha * 0.5)))
            glow.setColorAt(1.0, QColor(255, 200, 100, 0))
            
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(light_x - 35), int(light_y - 35), 70, 70)
            
            # Light beam
            beam = QPainterPath()
            beam.moveTo(light_x + 8, light_y - 6)
            beam.lineTo(light_x + 80, light_y - 20)
            beam.lineTo(light_x + 80, light_y + 20)
            beam.lineTo(light_x + 8, light_y + 6)
            beam.closeSubpath()
            
            beam_gradient = QLinearGradient(light_x, light_y, light_x + 80, light_y)
            beam_gradient.setColorAt(0.0, QColor(255, 255, 200, 40))
            beam_gradient.setColorAt(1.0, QColor(255, 255, 200, 0))
            painter.fillPath(beam, QBrush(beam_gradient))
        
        # Headlight housing (brass)
        housing_gradient = QRadialGradient(light_x, light_y, 10)
        housing_gradient.setColorAt(0.0, self.brass_color.lighter(150))
        housing_gradient.setColorAt(1.0, self.brass_color.darker(110))
        
        painter.setBrush(QBrush(housing_gradient))
        painter.setPen(QPen(self.copper_color, 1.5))
        painter.drawEllipse(int(light_x - 10), int(light_y - 10), 20, 20)
        
        # Light lens
        lens_gradient = QRadialGradient(light_x - 2, light_y - 2, 6)
        lens_gradient.setColorAt(0.0, QColor(255, 255, 240))
        lens_gradient.setColorAt(1.0, QColor(255, 255, 200))
        painter.setBrush(QBrush(lens_gradient))
        painter.drawEllipse(int(light_x - 6), int(light_y - 6), 12, 12)
        
        # === BRASS WHISTLE ===
        whistle_x = -30
        whistle_y = -38
        
        painter.setBrush(QBrush(self.brass_color))
        painter.setPen(QPen(self.copper_color, 1.0))
        
        # Whistle base
        painter.drawRect(whistle_x - 3, whistle_y + 8, 6, 8)
        # Whistle pipes
        painter.drawRect(whistle_x - 6, whistle_y, 4, 12)
        painter.drawRect(whistle_x + 2, whistle_y, 4, 12)
        # Whistle tops
        painter.drawEllipse(whistle_x - 7, whistle_y - 3, 6, 5)
        painter.drawEllipse(whistle_x + 1, whistle_y - 3, 6, 5)
        
        # Whistle steam (when active)
        if self.whistle_active:
            whistle_glow = QRadialGradient(whistle_x, whistle_y - 10, 20)
            whistle_glow.setColorAt(0.0, QColor(255, 255, 255, 100))
            whistle_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(whistle_glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(whistle_x - 20), int(whistle_y - 30), 40, 40)
        
        # === BRASS BELL ===
        bell_x = -5
        bell_y = -32
        
        bell_gradient = QRadialGradient(bell_x, bell_y, 8)
        bell_gradient.setColorAt(0.0, self.brass_color.lighter(140))
        bell_gradient.setColorAt(0.5, self.brass_color)
        bell_gradient.setColorAt(1.0, self.brass_color.darker(120))
        
        painter.setBrush(QBrush(bell_gradient))
        painter.setPen(QPen(self.copper_color, 1.0))
        painter.drawEllipse(int(bell_x - 8), int(bell_y - 8), 16, 14)
        
        # Bell mount
        painter.drawRect(bell_x - 2, bell_y + 4, 4, 6)
        
        # === RUST PATCHES (weathering) ===
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(5):
            rx = random.uniform(-60, 50)
            ry = random.uniform(-15, 20)
            painter.setBrush(QBrush(self.rust_color))
            painter.drawEllipse(int(rx - 5), int(ry - 3), 10, 6)
        
        # === NUMBER PLATE ===
        painter.setBrush(QBrush(self.brass_color))
        painter.setPen(QPen(self.copper_color, 1.0))
        painter.drawRect(35, 8, 16, 8)
        
        # Number "88"
        painter.setPen(QPen(QColor(40, 35, 25), 1.5))
        font = QFont("Arial", 6, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(38, 15, "88")
        
        painter.restore()
