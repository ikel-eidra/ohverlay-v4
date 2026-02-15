"""
Standalone preview for the Ethereal Cyan Jellyfish skin.
Opens a dark window with the animated jellyfish so you can see
the look and movement before wiring it into the full app.

Usage:
    python preview_cyan_jellyfish.py
"""

import sys
import math
import random
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QBrush

# Import the skin from the project
sys.path.insert(0, ".")
from ui.jellyfish_cyan_skin import CyanJellyfishSkin


class PreviewWindow(QWidget):
    """Dark window that renders the jellyfish swimming around."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyan Jellyfish Preview")
        self.resize(900, 700)
        self.setMinimumSize(600, 500)

        # Dark background
        self.setStyleSheet("background-color: #030818;")

        # Create the skin
        self.skin = CyanJellyfishSkin()
        self.skin.size_scale = 1.8  # Bigger for preview

        # Simulated position & movement
        self.jelly_x = 450.0
        self.jelly_y = 280.0
        self.vx = 0.0
        self.vy = 0.0
        self.target_x = 450.0
        self.target_y = 280.0
        self.time = 0.0

        # Wander timer - pick new target periodically
        self._pick_target()

        # 30 FPS render loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

        # Pick a new wander target every few seconds
        self.wander_timer = QTimer(self)
        self.wander_timer.timeout.connect(self._pick_target)
        self.wander_timer.start(4000)

    def _pick_target(self):
        """Choose a random point for the jellyfish to drift toward."""
        w = self.width()
        h = self.height()
        margin = 120
        self.target_x = random.uniform(margin, w - margin)
        self.target_y = random.uniform(margin, h - margin - 80)

    def _tick(self):
        dt = 0.033
        self.time += dt

        # Gentle drift toward target
        dx = self.target_x - self.jelly_x
        dy = self.target_y - self.jelly_y
        dist = math.hypot(dx, dy)
        if dist > 5:
            ax = (dx / dist) * 25
            ay = (dy / dist) * 25
            self.vx += ax * dt
            self.vy += ay * dt

        # Organic micro-drift
        self.vx += math.sin(self.time * 0.7) * 3 * dt
        self.vy += math.cos(self.time * 0.5) * 3 * dt

        # Damping
        self.vx *= 0.97
        self.vy *= 0.97

        self.jelly_x += self.vx * dt
        self.jelly_y += self.vy * dt

        # Keep in bounds
        w = self.width()
        h = self.height()
        self.jelly_x = max(80, min(w - 80, self.jelly_x))
        self.jelly_y = max(80, min(h - 120, self.jelly_y))

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Deep ocean gradient background
        w = self.width()
        h = self.height()
        bg_grad = QRadialGradient(w / 2, h / 2, max(w, h) * 0.7)
        bg_grad.setColorAt(0.0, QColor(5, 15, 40))
        bg_grad.setColorAt(0.5, QColor(3, 10, 28))
        bg_grad.setColorAt(1.0, QColor(1, 4, 12))
        painter.fillRect(self.rect(), QBrush(bg_grad))

        # Render the jellyfish
        fish_state = {
            "position": [self.jelly_x, self.jelly_y],
            "velocity": [self.vx, self.vy],
            "facing_angle": 0,
            "mood": 80,
        }
        self.skin.update_and_render(
            painter, self.jelly_x, self.jelly_y, 0, fish_state
        )

        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.skin.trigger_flash()
        elif event.key() == Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        # Click to set new target
        self.target_x = event.position().x()
        self.target_y = event.position().y()


def main():
    app = QApplication(sys.argv)
    win = PreviewWindow()
    win.show()
    print("Cyan Jellyfish Preview")
    print("  SPACE = trigger flash    CLICK = set target    ESC = quit")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
