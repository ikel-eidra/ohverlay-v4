"""
System tray icon and menu for Ohverlay.
Provides a minimal fallback right-click menu and left-click activation for the Control Center.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QPen
from PySide6.QtCore import Qt, Signal, QObject
import os
from utils.logger import logger


class TraySignals(QObject):
    """Signals emitted by tray actions."""
    open_control_center = Signal()
    show_welcome = Signal()
    toggle_visibility = Signal()
    quit_app = Signal()
    debug_canvas_extents = Signal()


class SystemTray(QSystemTrayIcon):
    """System tray icon with minimal fallback menu and left-click Control Center activation."""

    def __init__(self, config=None, overlay_manager=None, parent=None):
        super().__init__(parent)
        self.signals = TraySignals()
        self.config = config
        self.overlay_manager = overlay_manager

        self._create_icon()
        self._create_menu()
        self.setToolTip("Ohverlay — Nature Controls")
        self.activated.connect(self._on_activated)

    def _create_icon(self):
        """Generate the Ohverlay tray icon — a stylized 'O' with glow."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Outer glow
        glow = QRadialGradient(16, 16, 16)
        glow.setColorAt(0.0, QColor(80, 160, 255, 60))
        glow.setColorAt(0.7, QColor(60, 120, 255, 30))
        glow.setColorAt(1.0, QColor(40, 80, 200, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)

        # Ring (the "O")
        painter.setPen(QPen(QColor(100, 180, 255, 230), 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(7, 7, 18, 18)

        # Inner accent dot
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(140, 200, 255, 200))
        painter.drawEllipse(13, 13, 6, 6)

        painter.end()
        self.setIcon(QIcon(pixmap))

    def _create_menu(self):
        """Build minimal fallback right-click context menu."""
        menu = QMenu()

        header = menu.addAction("Ohverlay")
        header.setEnabled(False)
        menu.addSeparator()

        ctrl_action = menu.addAction("Open Nature Controls")
        ctrl_action.triggered.connect(self.signals.open_control_center.emit)

        visibility_action = menu.addAction("Toggle All Overlays (Ctrl+Alt+H)")
        visibility_action.triggered.connect(self.signals.toggle_visibility.emit)

        welcome_action = menu.addAction("Show Welcome Guide")
        welcome_action.triggered.connect(self.signals.show_welcome.emit)

        if os.environ.get("OHVERLAY_DEBUG") == "1":
            debug_action = menu.addAction("Debug: Show Canvas Extent")
            debug_action.triggered.connect(self.signals.debug_canvas_extents.emit)

        menu.addSeparator()

        quit_action = menu.addAction("Quit Ohverlay")
        quit_action.triggered.connect(self.signals.quit_app.emit)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        """Handle tray icon clicks."""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.signals.open_control_center.emit()
