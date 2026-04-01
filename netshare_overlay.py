"""
NetShare Overlay Window — transparent full-screen window that renders notification
bubbles. No fish, no creatures. Pure notification display.

One overlay per monitor. All share the same BubbleSystem.
Bubbles spawn from the bottom-centre of each screen.
"""

import time
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor

from ui.bubbles import BubbleSystem


class NetShareOverlay(QWidget):
    """
    Transparent, click-through, frameless overlay window.
    Paints notification bubbles from the shared BubbleSystem.
    """

    def __init__(self, screen_geometry, bubble_system: BubbleSystem, parent=None):
        super().__init__(parent)
        self.bubble_system = bubble_system
        self._geo = screen_geometry
        self._last_update = time.time()

        # Spawn point: bottom-centre of this screen (where bubbles rise from)
        self._spawn_x = screen_geometry.x() + screen_geometry.width() / 2
        self._spawn_y = screen_geometry.y() + screen_geometry.height() - 60

        # Transparent frameless always-on-top click-through overlay
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setGeometry(screen_geometry)

        # ~30 fps repaint + bubble physics update
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def _tick(self):
        now = time.time()
        dt = min(now - self._last_update, 0.1)
        self._last_update = now
        # Update bubble physics using spawn_x/y as the "fish" reference point
        self.bubble_system.update(dt, self._spawn_x, self._spawn_y)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Clear to fully transparent each frame (critical for Windows overlays)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Translate so bubble world coords map to this window's local space
        painter.translate(-self._geo.x(), -self._geo.y())
        self.bubble_system.render(painter)
        painter.end()

    def force_deliver_next(self):
        """Force-deliver the next queued bubble immediately."""
        self.bubble_system.force_deliver(self._spawn_x, self._spawn_y)
