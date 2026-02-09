"""
System tray icon and menu for ZenFish Overlay.
Provides settings, module toggles, color picker, sanctuary controls, and exit.
"""

from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu, QColorDialog, QInputDialog,
    QMessageBox, QApplication
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QRadialGradient, QBrush
from PySide6.QtCore import Qt, Signal, QObject
from utils.logger import logger


class TraySignals(QObject):
    """Signals emitted by tray actions for the main loop to handle."""
    color_changed = Signal(list, list, list)  # primary, secondary, accent
    sanctuary_toggled = Signal()
    sanctuary_add_monitor = Signal(int)
    sanctuary_clear = Signal()
    module_toggled = Signal(str, bool)
    feed_fish = Signal()
    toggle_visibility = Signal()
    quit_app = Signal()
    love_notes_path_set = Signal(str)
    size_changed = Signal(float)


class SystemTray(QSystemTrayIcon):
    """System tray icon with full settings menu."""

    # Preset color themes for the betta fish
    COLOR_PRESETS = {
        "Royal Blue": ([30, 80, 220], [60, 20, 180], [120, 140, 255]),
        "Crimson Red": ([200, 30, 40], [160, 20, 60], [255, 100, 80]),
        "Emerald Green": ([20, 160, 80], [10, 100, 120], [100, 255, 160]),
        "Purple Galaxy": ([120, 40, 200], [80, 20, 160], [200, 120, 255]),
        "Sunset Orange": ([240, 120, 30], [200, 60, 40], [255, 200, 100]),
        "Rose Pink": ([220, 80, 140], [180, 40, 120], [255, 160, 200]),
        "Teal Lagoon": ([30, 180, 180], [20, 120, 160], [100, 240, 240]),
        "Golden Koi": ([220, 180, 40], [200, 120, 20], [255, 230, 120]),
        "Midnight Black": ([40, 40, 60], [20, 20, 40], [80, 80, 120]),
        "Pearl White": ([200, 200, 210], [160, 170, 190], [240, 240, 255]),
    }

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.signals = TraySignals()
        self.config = config
        self._module_states = {
            "health": True,
            "love_notes": True,
            "schedule": True,
            "news": False,
        }

        if config:
            mods = config.get("modules")
            if isinstance(mods, dict):
                self._module_states.update(mods)

        self._create_icon()
        self._create_menu()
        self.setToolTip("ZenFish Overlay")

    def _create_icon(self):
        """Generate a simple fish icon for the tray."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fish body
        grad = QRadialGradient(14, 16, 12)
        grad.setColorAt(0.0, QColor(60, 120, 255, 230))
        grad.setColorAt(1.0, QColor(30, 60, 180, 200))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(6, 10, 20, 12)

        # Tail
        painter.setBrush(QColor(100, 160, 255, 200))
        from PySide6.QtGui import QPolygon
        from PySide6.QtCore import QPoint
        tail = QPolygon([QPoint(6, 16), QPoint(0, 8), QPoint(2, 16), QPoint(0, 24)])
        painter.drawPolygon(tail)

        # Eye
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.drawEllipse(20, 13, 5, 5)
        painter.setBrush(QColor(10, 10, 10, 240))
        painter.drawEllipse(22, 14, 3, 3)

        painter.end()
        self.setIcon(QIcon(pixmap))

    def _create_menu(self):
        """Build the tray context menu."""
        menu = QMenu()

        # --- Header ---
        header = menu.addAction("ZenFish Overlay")
        header.setEnabled(False)
        menu.addSeparator()

        # --- Fish Controls ---
        feed_action = menu.addAction("Feed Fish (Ctrl+Alt+F)")
        feed_action.triggered.connect(self.signals.feed_fish.emit)

        visibility_action = menu.addAction("Toggle Visibility (Ctrl+Alt+H)")
        visibility_action.triggered.connect(self.signals.toggle_visibility.emit)

        menu.addSeparator()

        # --- Color Submenu ---
        color_menu = menu.addMenu("Fish Colors")

        for name, (primary, secondary, accent) in self.COLOR_PRESETS.items():
            action = color_menu.addAction(name)
            action.triggered.connect(
                lambda checked, p=primary, s=secondary, a=accent:
                    self.signals.color_changed.emit(p, s, a)
            )

        color_menu.addSeparator()
        custom_action = color_menu.addAction("Custom Color...")
        custom_action.triggered.connect(self._pick_custom_color)

        # --- Size Submenu ---
        size_menu = menu.addMenu("Fish Size")
        for label, scale in [("Small", 0.7), ("Medium", 1.0), ("Large", 1.5), ("Extra Large", 2.0)]:
            action = size_menu.addAction(label)
            action.triggered.connect(
                lambda checked, s=scale: self.signals.size_changed.emit(s)
            )

        menu.addSeparator()

        # --- Sanctuary Mode ---
        sanctuary_menu = menu.addMenu("Sanctuary Mode")

        self._sanctuary_toggle = sanctuary_menu.addAction("Enable Sanctuary")
        self._sanctuary_toggle.setCheckable(True)
        self._sanctuary_toggle.setChecked(
            self.config.get("sanctuary", "enabled") if self.config else False
        )
        self._sanctuary_toggle.triggered.connect(self.signals.sanctuary_toggled.emit)

        sanctuary_menu.addSeparator()

        # Add monitor zones
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            geo = screen.geometry()
            action = sanctuary_menu.addAction(
                f"Exclude Monitor {i + 1} ({geo.width()}x{geo.height()})"
            )
            action.triggered.connect(
                lambda checked, idx=i: self.signals.sanctuary_add_monitor.emit(idx)
            )

        sanctuary_menu.addSeparator()
        clear_action = sanctuary_menu.addAction("Clear All Zones")
        clear_action.triggered.connect(self.signals.sanctuary_clear.emit)

        menu.addSeparator()

        # --- Module Toggles ---
        modules_menu = menu.addMenu("Bubble Modules")

        for mod_key, mod_label in [
            ("health", "Health Reminders"),
            ("love_notes", "Love Notes"),
            ("schedule", "Schedule Alerts"),
            ("news", "News Headlines"),
        ]:
            action = modules_menu.addAction(mod_label)
            action.setCheckable(True)
            action.setChecked(self._module_states.get(mod_key, False))
            action.triggered.connect(
                lambda checked, k=mod_key: self.signals.module_toggled.emit(k, checked)
            )

        modules_menu.addSeparator()
        love_path_action = modules_menu.addAction("Set Love Notes File...")
        love_path_action.triggered.connect(self._set_love_notes_path)

        menu.addSeparator()

        # --- Quit ---
        quit_action = menu.addAction("Quit ZenFish")
        quit_action.triggered.connect(self.signals.quit_app.emit)

        self.setContextMenu(menu)

    def _pick_custom_color(self):
        """Open color picker for custom primary color."""
        color = QColorDialog.getColor(
            QColor(*self.COLOR_PRESETS["Royal Blue"][0]),
            None, "Choose Primary Fish Color"
        )
        if color.isValid():
            primary = [color.red(), color.green(), color.blue()]
            # Generate complementary secondary and accent
            secondary = [
                max(0, primary[0] - 40),
                max(0, primary[1] - 40),
                min(255, primary[2] + 20)
            ]
            accent = [
                min(255, primary[0] + 60),
                min(255, primary[1] + 60),
                min(255, primary[2] + 40)
            ]
            self.signals.color_changed.emit(primary, secondary, accent)

    def _set_love_notes_path(self):
        """Prompt user for love notes JSON file path."""
        path, ok = QInputDialog.getText(
            None, "Love Notes",
            "Enter path to love notes JSON file:"
        )
        if ok and path:
            self.signals.love_notes_path_set.emit(path)

    def update_sanctuary_toggle(self, enabled):
        """Update the sanctuary toggle state in the menu."""
        self._sanctuary_toggle.setChecked(enabled)
