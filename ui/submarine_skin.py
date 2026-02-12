"""
Realistic Submarine v3.0 - Autonomous Screen Patrol
Roams across desktop, fires torpedoes every 20 minutes for eye rest
"""

import math
import random
from typing import List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QPen, QBrush, QFont
)
from PySide6.QtWidgets import QWidget
from dataclasses import dataclass, field


@dataclass
class Torpedo:
    """Active torpedo projectile"""
    x: float
    y: float
    angle: float
    speed: float = 10.0
    life: float = 8.0
    wake_points: List[Tuple[float, float]] = field(default_factory=list)


class RealisticSubmarine(QWidget):
    """
    Autonomous nuclear submarine that patrols the desktop
    Fires torpedoes every 20 minutes for 20-20-20 eye rest reminder
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
        
        # Screen bounds (dual monitor support)
        self.bounds = [0, 0, 3840, 1080]
        
        # Position - start at center
        self.x = 1920.0
        self.y = 540.0
        self.angle = 0.0
        self.target_x = self.x
        self.target_y = self.y
        
        # Movement
        self.speed = 0.0
        self.max_speed = 2.5
        self.cruise_speed = 1.5
        
        # Patrol system
        self.patrol_points = []
        self.current_patrol_idx = 0
        self._generate_patrol_route()
        self.idle_timer = 0.0
        
        # Visual
        self.time = 0.0
        self.propeller_angle = 0.0
        self.depth = 0.0
        
        # Torpedoes
        self.torpedoes: List[Torpedo] = []
        self.torpedo_cooldown = 0.0
        
        # Bubbles
        self.bubbles: List[dict] = []
        
        # 20-20-20 Eye Rest
        self.eye_rest_timer = 0.0
        self.eye_rest_interval = 20 * 60  # 20 minutes
        self.show_reminder = False
        self.reminder_timer = 0.0
        
        # Colors
        self.hull_color = QColor(80, 85, 90)
        self.hull_highlight = QColor(110, 115, 120)
        self.hull_shadow = QColor(50, 53, 56)
        
        self.resize(300, 200)
        self.move(int(self.x - 150), int(self.y - 100))
    
    def _generate_patrol_route(self):
        """Generate patrol waypoints across the screen"""
        # Create a patrol route that covers the screen
        margin = 200
        width = self.bounds[2] - margin * 2
        height = self.bounds[3] - margin * 2
        
        # Generate random patrol points
        num_points = 6
        self.patrol_points = []
        for i in range(num_points):
            px = margin + (width * i / (num_points - 1))
            py = margin + random.uniform(0, height * 0.8)
            self.patrol_points.append((px, py))
        
        # Shuffle for interesting route
        random.shuffle(self.patrol_points)
        self.current_patrol_idx = 0
        self.target_x, self.target_y = self.patrol_points[0]
    
    def fire_torpedo(self):
        """Fire a torpedo"""
        if self.torpedo_cooldown > 0:
            return
        
        bow_offset = 80
        torpedo_x = self.x + math.cos(self.angle) * bow_offset
        torpedo_y = self.y + math.sin(self.angle) * bow_offset
        
        torpedo = Torpedo(
            x=torpedo_x,
            y=torpedo_y,
            angle=self.angle,
            speed=12.0,
            life=10.0
        )
        
        self.torpedoes.append(torpedo)
        self.torpedo_cooldown = 3.0
        
        # Bubble burst
        for _ in range(8):
            self.bubbles.append({
                'x': torpedo_x + random.uniform(-5, 5),
                'y': torpedo_y + random.uniform(-5, 5),
                'size': random.uniform(2, 5),
                'life': 1.0,
                'rise': random.uniform(1.0, 2.0)
            })
    
    def update_state(self, dt: float, cursor_x: float, cursor_y: float):
        """Update submarine - follows patrol route with occasional cursor interest"""
        self.time += dt
        
        # Update patrol target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Occasionally get interested in cursor (20% chance when close)
        cursor_dx = cursor_x - self.x
        cursor_dy = cursor_y - self.y
        cursor_dist = math.sqrt(cursor_dx*cursor_dx + cursor_dy*cursor_dy)
        
        if cursor_dist < 300 and random.random() < 0.02:
            # Temporarily interested in cursor
            self.target_angle = math.atan2(cursor_dy, cursor_dx)
            target_speed = self.cruise_speed * 0.5
        else:
            # Normal patrol behavior
            if distance < 50:
                # Reached waypoint, go to next
                self.current_patrol_idx = (self.current_patrol_idx + 1) % len(self.patrol_points)
                self.target_x, self.target_y = self.patrol_points[self.current_patrol_idx]
                # Sometimes idle at waypoint
                self.idle_timer = random.uniform(0, 2.0)
            
            if self.idle_timer > 0:
                self.idle_timer -= dt
                target_speed = 0.0
            else:
                self.target_angle = math.atan2(dy, dx)
                target_speed = self.cruise_speed
        
        # Smooth rotation
        angle_diff = self.target_angle - self.angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        self.angle += angle_diff * 2.0 * dt
        
        # Smooth speed change
        self.speed += (target_speed - self.speed) * 2.0 * dt
        
        # Move
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        # Keep in bounds
        margin = 100
        self.x = max(margin, min(self.bounds[2] - margin, self.x))
        self.y = max(margin, min(self.bounds[3] - margin, self.y))
        
        # Propeller animation
        self.propeller_angle += self.speed * 0.3
        
        # Update torpedoes
        self._update_torpedoes(dt)
        
        # Update bubbles
        self._update_bubbles(dt)
        
        # Torpedo cooldown
        if self.torpedo_cooldown > 0:
            self.torpedo_cooldown -= dt
        
        # 20-20-20 Eye Rest
        self.eye_rest_timer += dt
        if self.eye_rest_timer >= self.eye_rest_interval:
            self.eye_rest_timer = 0.0
            self.fire_torpedo()
            self.show_reminder = True
            self.reminder_timer = 10.0
        
        if self.show_reminder:
            self.reminder_timer -= dt
            if self.reminder_timer <= 0:
                self.show_reminder = False
        
        # Update window position
        self.move(int(self.x - 150), int(self.y - 100))
        self.update()
    
    def _update_torpedoes(self, dt: float):
        """Update torpedo positions"""
        for torpedo in self.torpedoes[:]:
            torpedo.x += math.cos(torpedo.angle) * torpedo.speed
            torpedo.y += math.sin(torpedo.angle) * torpedo.speed
            torpedo.life -= dt
            
            # Trail
            torpedo.wake_points.append((torpedo.x, torpedo.y))
            if len(torpedo.wake_points) > 20:
                torpedo.wake_points.pop(0)
            
            # Remove if out of bounds or expired
            if (torpedo.life <= 0 or 
                torpedo.x < -100 or torpedo.x > self.bounds[2] + 100 or
                torpedo.y < -100 or torpedo.y > self.bounds[3] + 100):
                self.torpedoes.remove(torpedo)
    
    def _update_bubbles(self, dt: float):
        """Update bubble particles"""
        for bubble in self.bubbles[:]:
            bubble['life'] -= dt * 0.5
            bubble['y'] -= bubble['rise']
            if bubble['life'] <= 0:
                self.bubbles.remove(bubble)
    
    def paintEvent(self, event):
        """Render submarine"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        cx = 150
        cy = 100
        
        # Eye rest reminder
        if self.show_reminder:
            self._draw_reminder(painter)
        
        # Draw torpedoes
        self._draw_torpedoes(painter)
        
        # Draw submarine
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(math.degrees(self.angle))
        
        self._draw_submarine_body(painter)
        
        painter.restore()
        
        # Draw bubbles
        self._draw_bubbles(painter)
    
    def _draw_reminder(self, painter: QPainter):
        """Draw 20-20-20 reminder"""
        bg = QRectF(20, 20, 260, 50)
        painter.fillRect(bg, QColor(0, 50, 100, 180))
        painter.setPen(QPen(QColor(100, 200, 255), 2))
        painter.drawRect(bg)
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(25, 40, "20-20-20 EYE REST!")
        painter.drawText(25, 60, f"Look away! {int(self.reminder_timer)}s")
    
    def _draw_submarine_body(self, painter: QPainter):
        """Draw the submarine"""
        # Shadow
        painter.setBrush(QBrush(QColor(0, 20, 40, 60)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(-70, 20, 140, 30)
        
        # Hull
        hull_grad = QLinearGradient(0, -15, 0, 15)
        hull_grad.setColorAt(0.0, self.hull_highlight)
        hull_grad.setColorAt(0.5, self.hull_color)
        hull_grad.setColorAt(1.0, self.hull_shadow)
        
        painter.setBrush(QBrush(hull_grad))
        painter.setPen(QPen(QColor(40, 43, 46), 2))
        
        # Main hull
        hull = QPainterPath()
        hull.moveTo(80, 0)
        hull.cubicTo(80, 12, 40, 15, -60, 12)
        hull.lineTo(-70, 8)
        hull.lineTo(-70, -8)
        hull.lineTo(-60, -12)
        hull.cubicTo(40, -15, 80, -12, 80, 0)
        hull.closeSubpath()
        painter.drawPath(hull)
        
        # Conning tower
        tower_grad = QLinearGradient(0, -25, 0, -5)
        tower_grad.setColorAt(0.0, self.hull_highlight)
        tower_grad.setColorAt(1.0, self.hull_shadow)
        painter.setBrush(QBrush(tower_grad))
        
        tower = QPainterPath()
        tower.moveTo(20, -12)
        tower.lineTo(40, -12)
        tower.lineTo(35, -30)
        tower.lineTo(5, -30)
        tower.closeSubpath()
        painter.drawPath(tower)
        
        # Periscope
        painter.setBrush(QBrush(QColor(70, 73, 76)))
        painter.drawRect(10, -45, 6, 20)
        painter.drawEllipse(8, -48, 10, 6)
        
        # Propeller
        painter.save()
        painter.translate(-70, 0)
        painter.rotate(math.degrees(self.propeller_angle))
        painter.setBrush(QBrush(QColor(100, 103, 106)))
        for i in range(5):
            painter.save()
            painter.rotate(i * 72)
            painter.drawRect(-2, -15, 4, 15)
            painter.restore()
        painter.restore()
        
        # Lights
        # Red port light
        red_glow = QRadialGradient(-40, -8, 8)
        red_glow.setColorAt(0.0, QColor(255, 50, 50, 150))
        red_glow.setColorAt(1.0, QColor(255, 0, 0, 0))
        painter.setBrush(QBrush(red_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(-48, -16, 16, 16)
        
        # Green starboard light
        green_glow = QRadialGradient(-40, 8, 8)
        green_glow.setColorAt(0.0, QColor(50, 255, 50, 150))
        green_glow.setColorAt(1.0, QColor(0, 255, 0, 0))
        painter.setBrush(QBrush(green_glow))
        painter.drawEllipse(-48, 0, 16, 16)
        
        # White stern light
        white_glow = QRadialGradient(-65, 0, 10)
        white_glow.setColorAt(0.0, QColor(255, 255, 255, 200))
        white_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(white_glow))
        painter.drawEllipse(-75, -10, 20, 20)
    
    def _draw_torpedoes(self, painter: QPainter):
        """Draw active torpedoes"""
        for torpedo in self.torpedoes:
            # Transform to screen space
            tx = torpedo.x - self.x + 150
            ty = torpedo.y - self.y + 100
            
            if not (0 <= tx <= 300 and 0 <= ty <= 200):
                continue
            
            painter.save()
            painter.translate(tx, ty)
            painter.rotate(math.degrees(torpedo.angle))
            
            # Torpedo body
            body = QPainterPath()
            body.moveTo(15, 0)
            body.lineTo(-10, -3)
            body.lineTo(-12, 0)
            body.lineTo(-10, 3)
            body.closeSubpath()
            
            painter.setBrush(QBrush(QColor(80, 83, 86)))
            painter.setPen(QPen(QColor(40, 43, 46), 1))
            painter.drawPath(body)
            
            # Glow
            glow = QRadialGradient(-10, 0, 8)
            glow.setColorAt(0.0, QColor(255, 200, 100, 150))
            glow.setColorAt(1.0, QColor(255, 150, 50, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(-14, -6, 12, 12)
            
            painter.restore()
    
    def _draw_bubbles(self, painter: QPainter):
        """Draw bubbles"""
        for bubble in self.bubbles:
            bx = bubble['x'] - self.x + 150
            by = bubble['y'] - self.y + 100
            
            if not (0 <= bx <= 300 and 0 <= by <= 200):
                continue
            
            size = bubble['size'] * bubble['life']
            alpha = int(150 * bubble['life'])
            
            grad = QRadialGradient(bx, by, size)
            grad.setColorAt(0.0, QColor(255, 255, 255, alpha))
            grad.setColorAt(1.0, QColor(200, 220, 255, 0))
            
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(bx - size), int(by - size), int(size * 2), int(size * 2))
