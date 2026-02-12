"""
Realistic Submarine v1.0 - Non-Biological Object
Fires torpedoes that travel to end of monitors
"""

import math
import random
from typing import List, Tuple, Optional
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QPen, QBrush, QFont
)
from PySide6.QtWidgets import QWidget
from dataclasses import dataclass


@dataclass
class Torpedo:
    """Active torpedo projectile"""
    x: float
    y: float
    angle: float  # Direction in radians
    speed: float = 8.0
    life: float = 5.0  # Seconds before detonation
    wake_points: List[Tuple[float, float]] = None
    
    def __post_init__(self):
        if self.wake_points is None:
            self.wake_points = []


class RealisticSubmarine(QWidget):
    """
    Realistic nuclear submarine with torpedo firing capability
    Designed for dual/triple monitor setups (up to 3840x1080)
    """
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        
        # Window setup - transparent, frameless, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Submarine state
        self.x = 1920.0  # Center of dual monitors
        self.y = 540.0   # Middle height
        self.angle = 0.0  # Facing direction
        self.target_angle = 0.0
        self.speed = 0.0
        self.max_speed = 3.0
        
        # Visual states
        self.depth = 0.0  # 0 = surface, 1 = deep
        self.target_depth = 0.0
        self.propeller_angle = 0.0
        self.periscope_extended = 0.0  # 0-1 extension
        
        # Animation timing
        self.time = 0.0
        self.bubble_timer = 0.0
        self.torpedo_cooldown = 0.0
        
        # Collections
        self.torpedoes: List[Torpedo] = []
        self.bubbles: List[dict] = []
        
        # Dimensions (scaled for visibility across monitors)
        self.sub_length = 180
        self.sub_width = 28
        
        # Color scheme - military grey with rust/wear
        self.hull_color = QColor(80, 85, 90)  # Military grey
        self.hull_highlight = QColor(110, 115, 120)
        self.hull_shadow = QColor(50, 53, 56)
        self.rust_color = QColor(120, 80, 50, 80)  # Subtle rust
        
        # Light effects
        self.running_lights = True
        self.light_blink_timer = 0.0
        self.light_on = True
        
        self.resize(250, 150)
        self.move(int(self.x - 125), int(self.y - 75))
    
    def fire_torpedo(self):
        """Fire a torpedo from the bow"""
        if self.torpedo_cooldown > 0:
            return
        
        # Calculate bow position (front of submarine)
        bow_offset = self.sub_length * 0.45
        torpedo_x = self.x + math.cos(self.angle) * bow_offset
        torpedo_y = self.y + math.sin(self.angle) * bow_offset
        
        # Create torpedo
        torpedo = Torpedo(
            x=torpedo_x,
            y=torpedo_y,
            angle=self.angle,
            speed=12.0,
            life=8.0,
            wake_points=[(torpedo_x, torpedo_y)]
        )
        
        self.torpedoes.append(torpedo)
        self.torpedo_cooldown = 2.0  # 2 second cooldown
        
        # Add bubble burst at firing
        for _ in range(10):
            self.bubbles.append({
                'x': torpedo_x + random.uniform(-5, 5),
                'y': torpedo_y + random.uniform(-5, 5),
                'size': random.uniform(2, 6),
                'life': 1.0,
                'rise_speed': random.uniform(1.0, 2.5)
            })
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update submarine state"""
        self.time += dt
        
        # Calculate angle to target
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 10:
            self.target_angle = math.atan2(dy, dx)
            
            # Smooth rotation
            angle_diff = self.target_angle - self.angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            self.angle += angle_diff * 2.0 * dt
            
            # Speed based on distance
            target_speed = min(self.max_speed, distance * 0.5)
            self.speed += (target_speed - self.speed) * 2.0 * dt
        else:
            self.speed *= 0.9
        
        # Move submarine
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        # Keep in bounds
        self.x = max(100, min(3740, self.x))
        self.y = max(100, min(980, self.y))
        
        # Update propeller
        self.propeller_angle += self.speed * 0.5 * dt
        
        # Periscope extension based on depth
        self.target_depth = 0.0 if random.random() > 0.7 else 0.3
        self.depth += (self.target_depth - self.depth) * 0.5 * dt
        self.periscope_extended = 1.0 - self.depth
        
        # Update torpedo cooldown
        if self.torpedo_cooldown > 0:
            self.torpedo_cooldown -= dt
        
        # Random torpedo fire chance (when moving fast)
        if self.speed > 1.5 and random.random() < 0.005:
            self.fire_torpedo()
        
        # Update torpedoes
        self._update_torpedoes(dt)
        
        # Update bubbles
        self._update_bubbles(dt)
        
        # Running lights blink
        self.light_blink_timer += dt
        if self.light_blink_timer > 1.0:
            self.light_blink_timer = 0.0
            self.light_on = not self.light_on
        
        # Update window position
        self.move(int(self.x - 125), int(self.y - 75))
        self.update()
    
    def _update_torpedoes(self, dt: float):
        """Update all active torpedoes"""
        for torpedo in self.torpedoes[:]:
            # Move torpedo
            torpedo.x += math.cos(torpedo.angle) * torpedo.speed
            torpedo.y += math.sin(torpedo.angle) * torpedo.speed
            
            # Update life
            torpedo.life -= dt
            
            # Add wake point
            torpedo.wake_points.append((torpedo.x, torpedo.y))
            if len(torpedo.wake_points) > 20:
                torpedo.wake_points.pop(0)
            
            # Create bubble trail
            if random.random() < 0.3:
                self.bubbles.append({
                    'x': torpedo.x + random.uniform(-3, 3),
                    'y': torpedo.y + random.uniform(-3, 3),
                    'size': random.uniform(1, 3),
                    'life': 0.8,
                    'rise_speed': random.uniform(0.5, 1.5)
                })
            
            # Remove if out of bounds or expired
            if (torpedo.life <= 0 or 
                torpedo.x < -100 or torpedo.x > 3940 or
                torpedo.y < -100 or torpedo.y > 1180):
                self.torpedoes.remove(torpedo)
    
    def _update_bubbles(self, dt: float):
        """Update bubble particles"""
        for bubble in self.bubbles[:]:
            bubble['life'] -= dt
            bubble['y'] -= bubble['rise_speed']
            bubble['x'] += math.sin(self.time * 3 + bubble['y'] * 0.1) * 0.5
            
            if bubble['life'] <= 0:
                self.bubbles.remove(bubble)
    
    def paintEvent(self, event):
        """Render submarine and torpedoes"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background with transparent
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        center_x = 125
        center_y = 75
        
        # Save painter state
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(math.degrees(self.angle))
        
        # Draw submarine shadow
        self._draw_shadow(painter)
        
        # Draw hull
        self._draw_hull(painter)
        
        # Draw conning tower
        self._draw_conning_tower(painter)
        
        # Draw propeller
        self._draw_propeller(painter)
        
        # Draw running lights
        self._draw_running_lights(painter)
        
        # Restore for torpedoes (world space)
        painter.restore()
        
        # Draw torpedoes (in screen space)
        self._draw_torpedoes(painter)
        
        # Draw bubbles
        self._draw_bubbles(painter)
    
    def _draw_shadow(self, painter: QPainter):
        """Draw submarine shadow on seafloor"""
        shadow_offset = 15 + self.depth * 30
        shadow_color = QColor(0, 20, 40, 60)
        
        painter.save()
        painter.translate(shadow_offset, shadow_offset * 0.5)
        
        path = QPainterPath()
        path.addEllipse(
            -self.sub_length * 0.45,
            -self.sub_width * 0.4,
            self.sub_length * 0.9,
            self.sub_width * 0.8
        )
        
        # Conning tower shadow
        path.addRect(
            -self.sub_length * 0.1,
            -self.sub_width * 0.6 - self.periscope_extended * 20,
            self.sub_length * 0.25,
            self.sub_width * 0.5 + self.periscope_extended * 20
        )
        
        painter.fillPath(path, QBrush(shadow_color))
        painter.restore()
    
    def _draw_hull(self, painter: QPainter):
        """Draw main submarine hull"""
        # Hull gradient
        gradient = QLinearGradient(0, -self.sub_width * 0.5, 0, self.sub_width * 0.5)
        gradient.setColorAt(0.0, self.hull_highlight)
        gradient.setColorAt(0.3, self.hull_color)
        gradient.setColorAt(0.7, self.hull_color)
        gradient.setColorAt(1.0, self.hull_shadow)
        
        # Main hull shape - teardrop/cylinder hybrid
        hull_path = QPainterPath()
        
        # Bow (front) - rounded
        bow_x = self.sub_length * 0.45
        bow_curve = self.sub_width * 0.3
        
        # Stern (back) - tapered
        stern_x = -self.sub_length * 0.45
        
        # Top curve
        hull_path.moveTo(stern_x, 0)
        hull_path.cubicTo(
            stern_x + self.sub_length * 0.2, -self.sub_width * 0.45,
            bow_x - self.sub_length * 0.3, -self.sub_width * 0.5,
            bow_x, 0
        )
        
        # Bottom curve
        hull_path.cubicTo(
            bow_x - self.sub_length * 0.3, self.sub_width * 0.5,
            stern_x + self.sub_length * 0.2, self.sub_width * 0.45,
            stern_x, 0
        )
        
        hull_path.closeSubpath()
        
        # Fill hull
        painter.fillPath(hull_path, QBrush(gradient))
        
        # Hull outline
        pen = QPen(QColor(40, 43, 46), 1.5)
        painter.setPen(pen)
        painter.drawPath(hull_path)
        
        # Hull details - rivet lines
        painter.setPen(QPen(QColor(60, 63, 66), 1.0))
        for i in range(4):
            y_offset = -self.sub_width * 0.3 + i * self.sub_width * 0.2
            painter.drawLine(
                int(stern_x + 10), int(y_offset),
                int(bow_x - 10), int(y_offset)
            )
        
        # Rust patches (subtle weathering)
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(5):
            rust_x = stern_x + self.sub_length * (0.2 + i * 0.15)
            rust_y = -self.sub_width * 0.2 + random.uniform(-3, 3)
            painter.setBrush(QBrush(self.rust_color))
            painter.drawEllipse(
                int(rust_x - 8), int(rust_y - 4),
                16, 8
            )
        
        # Bow sonar dome
        sonar_gradient = QRadialGradient(
            bow_x - 5, 0, self.sub_width * 0.4
        )
        sonar_gradient.setColorAt(0.0, QColor(100, 105, 110))
        sonar_gradient.setColorAt(1.0, self.hull_color)
        
        painter.setBrush(QBrush(sonar_gradient))
        painter.setPen(QPen(QColor(50, 53, 56), 1.0))
        painter.drawEllipse(
            int(bow_x - self.sub_width * 0.35),
            int(-self.sub_width * 0.35),
            int(self.sub_width * 0.7),
            int(self.sub_width * 0.7)
        )
    
    def _draw_conning_tower(self, painter: QPainter):
        """Draw conning tower (sail) with periscope"""
        tower_width = self.sub_width * 0.7
        tower_length = self.sub_length * 0.25
        tower_x = -self.sub_length * 0.05
        tower_y = -self.sub_width * 0.5
        
        # Tower gradient
        tower_gradient = QLinearGradient(0, tower_y - 15, 0, tower_y)
        tower_gradient.setColorAt(0.0, self.hull_highlight)
        tower_gradient.setColorAt(1.0, self.hull_shadow)
        
        # Tower shape
        tower_path = QPainterPath()
        tower_path.moveTo(tower_x - tower_length * 0.3, tower_y)
        tower_path.lineTo(tower_x + tower_length * 0.7, tower_y)
        tower_path.lineTo(tower_x + tower_length * 0.6, tower_y - 20)
        tower_path.lineTo(tower_x - tower_length * 0.2, tower_y - 20)
        tower_path.closeSubpath()
        
        painter.fillPath(tower_path, QBrush(tower_gradient))
        painter.setPen(QPen(QColor(40, 43, 46), 1.5))
        painter.drawPath(tower_path)
        
        # Periscope
        scope_height = 25 + self.periscope_extended * 20
        scope_x = tower_x + tower_length * 0.3
        
        # Periscope shaft
        painter.setBrush(QBrush(QColor(70, 73, 76)))
        painter.setPen(QPen(QColor(40, 43, 46), 1.0))
        painter.drawRect(
            int(scope_x - 3), int(tower_y - scope_height),
            6, int(scope_height)
        )
        
        # Periscope head (rotated based on angle)
        head_y = tower_y - scope_height
        painter.setBrush(QBrush(QColor(90, 93, 96)))
        painter.drawEllipse(
            int(scope_x - 5), int(head_y - 4),
            10, 8
        )
        
        # Periscope lens (blue reflection)
        lens_gradient = QRadialGradient(scope_x + 2, head_y, 3)
        lens_gradient.setColorAt(0.0, QColor(150, 200, 255))
        lens_gradient.setColorAt(1.0, QColor(50, 100, 150))
        painter.setBrush(QBrush(lens_gradient))
        painter.drawEllipse(
            int(scope_x + 1), int(head_y - 2),
            4, 4
        )
        
        # Dive planes on tower
        painter.setBrush(QBrush(self.hull_color))
        painter.setPen(QPen(QColor(40, 43, 46), 1.0))
        # Front dive plane
        painter.drawRect(
            int(tower_x + tower_length * 0.5), int(tower_y - 5),
            20, 4
        )
    
    def _draw_propeller(self, painter: QPainter):
        """Draw rotating propeller at stern"""
        stern_x = -self.sub_length * 0.45
        
        # Propeller hub
        painter.setBrush(QBrush(QColor(60, 63, 66)))
        painter.setPen(QPen(QColor(30, 33, 36), 1.0))
        painter.drawEllipse(
            int(stern_x - 6), int(-6),
            12, 12
        )
        
        # Propeller blades (rotating)
        painter.save()
        painter.translate(stern_x - 3, 0)
        painter.rotate(math.degrees(self.propeller_angle))
        
        painter.setBrush(QBrush(QColor(100, 103, 106)))
        painter.setPen(QPen(QColor(50, 53, 56), 1.0))
        
        # 5 blades
        for i in range(5):
            painter.save()
            painter.rotate(i * 72)
            
            # Blade shape
            blade = QPainterPath()
            blade.moveTo(0, 0)
            blade.quadTo(5, -8, 8, -15)
            blade.lineTo(10, -14)
            blade.quadTo(8, -6, 3, 0)
            blade.closeSubpath()
            
            painter.fillPath(blade, QBrush(QColor(120, 123, 126)))
            painter.drawPath(blade)
            
            painter.restore()
        
        painter.restore()
        
        # Propeller blur effect when spinning fast
        if abs(self.speed) > 1.0:
            blur_alpha = min(100, int(abs(self.speed) * 30))
            blur_color = QColor(150, 155, 160, blur_alpha)
            painter.setBrush(QBrush(blur_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(stern_x - 15), int(-15),
                30, 30
            )
    
    def _draw_running_lights(self, painter: QPainter):
        """Draw navigation lights (blink)"""
        if not self.light_on:
            return
        
        # Port (left) - red
        port_gradient = QRadialGradient(-self.sub_length * 0.3, -self.sub_width * 0.3, 8)
        port_gradient.setColorAt(0.0, QColor(255, 50, 50, 200))
        port_gradient.setColorAt(1.0, QColor(255, 0, 0, 0))
        painter.setBrush(QBrush(port_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(-self.sub_length * 0.3 - 8), int(-self.sub_width * 0.3 - 8),
            16, 16
        )
        
        # Starboard (right) - green
        star_gradient = QRadialGradient(-self.sub_length * 0.3, self.sub_width * 0.3, 8)
        star_gradient.setColorAt(0.0, QColor(50, 255, 50, 200))
        star_gradient.setColorAt(1.0, QColor(0, 255, 0, 0))
        painter.setBrush(QBrush(star_gradient))
        painter.drawEllipse(
            int(-self.sub_length * 0.3 - 8), int(self.sub_width * 0.3 - 8),
            16, 16
        )
    
    def _draw_torpedoes(self, painter: QPainter):
        """Draw active torpedoes"""
        # Transform from world to screen coordinates
        sub_screen_x = self.x - self.pos().x()
        sub_screen_y = self.y - self.pos().y()
        
        for torpedo in self.torpedoes:
            # Calculate screen position relative to submarine widget
            tx = torpedo.x - self.pos().x()
            ty = torpedo.y - self.pos().y()
            
            # Skip if too far
            if abs(tx - 125) > 2000 or abs(ty - 75) > 1000:
                continue
            
            painter.save()
            painter.translate(tx, ty)
            painter.rotate(math.degrees(torpedo.angle))
            
            # Torpedo body
            torp_gradient = QLinearGradient(-15, 0, 15, 0)
            torp_gradient.setColorAt(0.0, QColor(80, 83, 86))
            torp_gradient.setColorAt(0.5, QColor(120, 123, 126))
            torp_gradient.setColorAt(1.0, QColor(60, 63, 66))
            
            body_path = QPainterPath()
            body_path.moveTo(18, 0)
            body_path.lineTo(-12, -4)
            body_path.lineTo(-15, 0)
            body_path.lineTo(-12, 4)
            body_path.closeSubpath()
            
            painter.fillPath(body_path, QBrush(torp_gradient))
            painter.setPen(QPen(QColor(40, 43, 46), 1.0))
            painter.drawPath(body_path)
            
            # Propeller glow at rear
            glow_gradient = QRadialGradient(-15, 0, 6)
            glow_gradient.setColorAt(0.0, QColor(255, 200, 100, 180))
            glow_gradient.setColorAt(1.0, QColor(255, 150, 50, 0))
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(-18), int(-6),
                12, 12
            )
            
            # Propeller blur
            painter.setBrush(QBrush(QColor(200, 200, 200, 100)))
            painter.drawEllipse(
                int(-16), int(-5),
                4, 10
            )
            
            painter.restore()
            
            # Draw wake trail
            if len(torpedo.wake_points) > 1:
                wake_color = QColor(200, 220, 255, 60)
                painter.setPen(QPen(wake_color, 2.0))
                for i in range(len(torpedo.wake_points) - 1):
                    p1 = torpedo.wake_points[i]
                    p2 = torpedo.wake_points[i + 1]
                    x1 = p1[0] - self.pos().x()
                    y1 = p1[1] - self.pos().y()
                    x2 = p2[0] - self.pos().x()
                    y2 = p2[1] - self.pos().y()
                    
                    # Only draw if within reasonable range
                    if abs(x1 - 125) < 1000 and abs(y1 - 75) < 600:
                        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_bubbles(self, painter: QPainter):
        """Draw bubble particles"""
        for bubble in self.bubbles:
            bx = bubble['x'] - self.pos().x()
            by = bubble['y'] - self.pos().y()
            
            # Skip if too far
            if abs(bx - 125) > 1000 or abs(by - 75) > 600:
                continue
            
            alpha = int(150 * bubble['life'])
            size = bubble['size'] * bubble['life']
            
            bubble_gradient = QRadialGradient(bx - size*0.3, by - size*0.3, size)
            bubble_gradient.setColorAt(0.0, QColor(255, 255, 255, alpha))
            bubble_gradient.setColorAt(0.7, QColor(200, 220, 255, alpha * 0.5))
            bubble_gradient.setColorAt(1.0, QColor(150, 180, 220, 0))
            
            painter.setBrush(QBrush(bubble_gradient))
            painter.setPen(QPen(QColor(255, 255, 255, alpha * 0.5), 0.5))
            painter.drawEllipse(
                int(bx - size), int(by - size),
                int(size * 2), int(size * 2)
            )


class SubmarineTorpedoOverlay(QWidget):
    """
    Separate overlay for torpedoes that travel across entire monitor space
    This allows torpedoes to continue even when submarine turns
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.torpedoes: List[Torpedo] = []
        self.setGeometry(0, 0, 3840, 1080)
    
    def add_torpedo(self, torpedo: Torpedo):
        """Add a torpedo to the overlay"""
        self.torpedoes.append(torpedo)
    
    def update_torpedoes(self, dt: float):
        """Update all torpedoes"""
        for torpedo in self.torpedoes[:]:
            torpedo.x += math.cos(torpedo.angle) * torpedo.speed
            torpedo.y += math.sin(torpedo.angle) * torpedo.speed
            torpedo.life -= dt
            
            # Add wake point
            torpedo.wake_points.append((torpedo.x, torpedo.y))
            if len(torpedo.wake_points) > 30:
                torpedo.wake_points.pop(0)
            
            # Remove if out of bounds or expired
            if (torpedo.life <= 0 or 
                torpedo.x < -200 or torpedo.x > 4040 or
                torpedo.y < -200 or torpedo.y > 1280):
                self.torpedoes.remove(torpedo)
        
        self.update()
    
    def paintEvent(self, event):
        """Render torpedoes across full monitor space"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        for torpedo in self.torpedoes:
            painter.save()
            painter.translate(torpedo.x, torpedo.y)
            painter.rotate(math.degrees(torpedo.angle))
            
            # Torpedo body
            torp_gradient = QLinearGradient(-15, 0, 15, 0)
            torp_gradient.setColorAt(0.0, QColor(80, 83, 86))
            torp_gradient.setColorAt(0.5, QColor(120, 123, 126))
            torp_gradient.setColorAt(1.0, QColor(60, 63, 66))
            
            body_path = QPainterPath()
            body_path.moveTo(20, 0)
            body_path.quadTo(10, -5, -10, -5)
            body_path.lineTo(-18, 0)
            body_path.lineTo(-10, 5)
            body_path.quadTo(10, 5, 20, 0)
            body_path.closeSubpath()
            
            painter.fillPath(body_path, QBrush(torp_gradient))
            painter.setPen(QPen(QColor(40, 43, 46), 1.0))
            painter.drawPath(body_path)
            
            # Propeller glow
            glow_gradient = QRadialGradient(-18, 0, 8)
            glow_gradient.setColorAt(0.0, QColor(255, 200, 100, 200))
            glow_gradient.setColorAt(0.5, QColor(255, 100, 50, 100))
            glow_gradient.setColorAt(1.0, QColor(255, 50, 0, 0))
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(-22), int(-8),
                16, 16
            )
            
            painter.restore()
            
            # Wake trail
            if len(torpedo.wake_points) > 1:
                for i in range(len(torpedo.wake_points) - 1):
                    p1 = torpedo.wake_points[i]
                    p2 = torpedo.wake_points[i + 1]
                    alpha = int(100 * (i / len(torpedo.wake_points)) * (torpedo.life / 8.0))
                    painter.setPen(QPen(QColor(200, 220, 255, alpha), 3.0 - i * 0.08))
                    painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
