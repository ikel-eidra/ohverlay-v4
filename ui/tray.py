"""
System tray icon and menu for Ohverlay.
Minimal Nature Baseline.
"""

from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QBrush, QPen, QActionGroup
from PySide6.QtCore import Qt, Signal, QObject
import os
from utils.logger import logger


class TraySignals(QObject):
    """Signals emitted by tray actions."""
    toggle_visibility = Signal()
    quit_app = Signal()
    overlay_toggled = Signal(str)   # overlay_id
    debug_canvas_extents = Signal()


class SystemTray(QSystemTrayIcon):
    """System tray icon with overlay management menu."""

    def __init__(self, config=None, overlay_manager=None, parent=None):
        super().__init__(parent)
        self.signals = TraySignals()
        self.config = config
        self.overlay_manager = overlay_manager
        self._overlay_actions = {}  # overlay_id -> QAction

        self._create_icon()
        self._create_menu()
        self.setToolTip("Ohverlay — Minimal Nature Baseline")

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
        painter.setBrush(QBrush(glow))
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
        """Build the tray context menu."""
        menu = QMenu()

        # ── Header ──
        header = menu.addAction("Ohverlay")
        header.setEnabled(False)
        menu.addSeparator()

        # ── Overlays ──
        overlay_menu = menu.addMenu("Overlays")

        if self.overlay_manager and self.overlay_manager.available:
            amb_header = overlay_menu.addAction("— Nature Overlays —")
            amb_header.setEnabled(False)

            for ov in self.overlay_manager.get_registry():
                self._add_overlay_action(overlay_menu, ov)
        else:
            no_engine = overlay_menu.addAction("Install PySide6-WebEngine for overlays")
            no_engine.setEnabled(False)

        # ── Overlay Settings ──
        settings_menu = menu.addMenu("Overlay Settings")
        size_menu = settings_menu.addMenu("Object Size")
        
        self._setup_size_submenu(size_menu, "Dragonflies", "dragonflies")
        self._setup_size_submenu(size_menu, "Dandelions", "dandelions")
        self._setup_size_submenu(size_menu, "Fireflies", "fireflies")

        menu.addSeparator()
        visibility_action = menu.addAction("Toggle All Overlays (Ctrl+Alt+H)")
        visibility_action.triggered.connect(self.signals.toggle_visibility.emit)

        if os.environ.get("OHVERLAY_DEBUG") == "1":
            debug_action = menu.addAction("Debug: Show Canvas Extent")
            debug_action.triggered.connect(self.signals.debug_canvas_extents.emit)

        menu.addSeparator()

        # ── Quit ──
        quit_action = menu.addAction("Quit Ohverlay")
        quit_action.triggered.connect(self.signals.quit_app.emit)

        self.setContextMenu(menu)

    def _add_overlay_action(self, menu, overlay_info):
        """Add a checkable overlay toggle to the menu."""
        action = menu.addAction(overlay_info["name"])
        action.setCheckable(True)
        action.setToolTip(overlay_info.get("description", ""))

        # Check if overlay is currently active
        if self.overlay_manager:
            action.setChecked(self.overlay_manager.is_active(overlay_info["id"]))

        overlay_id = overlay_info["id"]
        action.triggered.connect(
            lambda checked, oid=overlay_id: self.signals.overlay_toggled.emit(oid)
        )

        self._overlay_actions[overlay_info["id"]] = action

    def update_overlay_state(self, overlay_id, active):
        """Update the checkmark state of an overlay in the menu."""
        if overlay_id in self._overlay_actions:
            self._overlay_actions[overlay_id].setChecked(active)

    def _setup_size_submenu(self, parent_menu, label_text, overlay_id):
        sub_menu = parent_menu.addMenu(label_text)
        group = QActionGroup(sub_menu)
        
        current_scale = 1.0
        if self.config:
            scale_val = self.config.get("overlays", f"{overlay_id}_scale")
            if scale_val is None:
                scale_val = self.config.get("overlays", "global_scale")
            current_scale = float(scale_val or 1.0)
            
        for label, val in [("Small (50%)", 0.5), ("Normal (100%)", 1.0), ("Large (150%)", 1.5)]:
            action = sub_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(abs(current_scale - val) < 0.01)
            group.addAction(action)
            action.triggered.connect(lambda checked, v=val, oid=overlay_id: self._set_scale_config(oid, v))

    def _set_scale_config(self, overlay_id, scale):
        """Update specific overlay scale and restart it to apply."""
        if self.config:
            self.config.set("overlays", f"{overlay_id}_scale", scale)
            self.config.save()
            
        if self.overlay_manager:
            active_ids = self.overlay_manager.get_active_ids()
            if overlay_id in active_ids:
                self.overlay_manager.close_overlay(overlay_id)
                self.overlay_manager.open_overlay(overlay_id)

