from PySide6.QtGui import QPainter, QColor, QPolygon, QPen, QLinearGradient
from PySide6.QtCore import QPoint, Qt
import numpy as np

class FishSkin:
    def __init__(self):
        self.tail_phase = 0.0
        self.glow_phase = 0.0

    def render(self, painter, local_pos, fish_state):
        x, y = local_pos
        vx, vy = fish_state["velocity"]
        # Calculate angle, default to 0 if not moving
        if abs(vx) < 0.1 and abs(vy) < 0.1:
            angle = 0
        else:
            angle = np.degrees(np.arctan2(vy, vx))

        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)

        # State-based parameters
        hunger = fish_state.get("hunger", 0)
        mood = fish_state.get("mood", 100)
        state = fish_state.get("state", "IDLE")

        # Cyber-Guerilla Color Palette
        base_cyan = QColor(0, 255, 255, 180)
        danger_red = QColor(255, 50, 50, 200)

        # Blend color based on hunger
        r = int((hunger / 100.0) * danger_red.red() + (1 - hunger / 100.0) * base_cyan.red())
        g = int((hunger / 100.0) * danger_red.green() + (1 - hunger / 100.0) * base_cyan.green())
        b = int((hunger / 100.0) * danger_red.blue() + (1 - hunger / 100.0) * base_cyan.blue())
        alpha = int(150 + (mood / 100.0) * 105)

        fish_color = QColor(r, g, b, alpha)

        # Animation speeds
        self.tail_phase += 0.2 * (1 + (np.linalg.norm([vx, vy]) / 200.0))
        self.glow_phase += 0.1

        # Draw Glow (Aura)
        glow_size = 40 + np.sin(self.glow_phase) * 10
        gradient = QLinearGradient(0, -glow_size, 0, glow_size)
        gradient.setColorAt(0, QColor(r, g, b, 0))
        gradient.setColorAt(0.5, QColor(r, g, b, 50))
        gradient.setColorAt(1, QColor(r, g, b, 0))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-30, -glow_size, 80, glow_size * 2)

        # Body
        painter.setBrush(fish_color)
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawEllipse(-25, -12, 50, 24)

        # Animated Tail
        tail_swing = np.sin(self.tail_phase) * 15
        tail = QPolygon([
            QPoint(-20, 0),
            QPoint(-60, int(-30 + tail_swing)),
            QPoint(-45, 0),
            QPoint(-60, int(30 + tail_swing))
        ])
        painter.drawPolygon(tail)

        # Fins (Dorsal & Pectoral)
        dorsal = QPolygon([
            QPoint(-10, -10),
            QPoint(-30, -35),
            QPoint(10, -10)
        ])
        painter.drawPolygon(dorsal)

        # Eye (Cybernetic)
        if hunger > 50:
            painter.setBrush(Qt.red)
        else:
            painter.setBrush(Qt.black)
        painter.drawEllipse(15, -6, 6, 6)
        painter.setBrush(Qt.white)
        painter.drawEllipse(18, -4, 2, 2)

        painter.restore()
