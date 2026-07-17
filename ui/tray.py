"""
System tray icon and menu for OHVERLAY v4.0.
Professional overlay platform — toggle overlays, manage modules and integrations.
"""

from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu, QInputDialog,
    QApplication
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QBrush, QPen, QActionGroup
from PySide6.QtCore import Qt, Signal, QObject
from utils.logger import logger


class TraySignals(QObject):
    """Signals emitted by tray actions."""
    sanctuary_toggled = Signal()
    sanctuary_add_monitor = Signal(int)
    sanctuary_clear = Signal()
    module_toggled = Signal(str, bool)
    toggle_visibility = Signal()
    quit_app = Signal()
    love_notes_path_set = Signal(str)
    telegram_token_set = Signal(str)
    webhook_toggled = Signal(bool)
    llm_key_set = Signal(str, str)  # provider, key
    overlay_toggled = Signal(str)   # overlay_id
    fish_settings_changed = Signal()
    debug_canvas_extents = Signal()


class SystemTray(QSystemTrayIcon):
    """System tray icon with overlay management menu."""

    def __init__(self, config=None, overlay_manager=None, parent=None):
        super().__init__(parent)
        self.signals = TraySignals()
        self.config = config
        self.overlay_manager = overlay_manager
        self._overlay_actions = {}  # overlay_id -> QAction
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
        self.setToolTip("Ohverlay v4.0 — Desktop Overlay Platform")

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
        header = menu.addAction("Ohverlay v4.0")
        header.setEnabled(False)
        menu.addSeparator()

        # ── Overlays ──
        overlay_menu = menu.addMenu("Overlays")

        if self.overlay_manager and self.overlay_manager.available:
            # Ambient overlays
            amb_header = overlay_menu.addAction("— Nature Overlays —")
            amb_header.setEnabled(False)

            for ov in self.overlay_manager.get_registry():
                if ov["category"] == "ambient":
                    self._add_overlay_action(overlay_menu, ov)
        else:
            no_engine = overlay_menu.addAction("Install PySide6-WebEngine for overlays")
            no_engine.setEnabled(False)

        # ── Overlay Settings ──
        settings_menu = menu.addMenu("Overlay Settings")
        size_menu = settings_menu.addMenu("Object Size")
        
        self._setup_size_submenu(size_menu, "Ecosystem Mode", "ecosystem")
        self._setup_size_submenu(size_menu, "Dragonflies", "dragonflies")
        self._setup_size_submenu(size_menu, "Dandelions", "dandelions")
        self._setup_size_submenu(size_menu, "Fireflies", "fireflies")
        self._setup_size_submenu(size_menu, "Hornwort", "hornwort")

        menu.addSeparator()
        visibility_action = menu.addAction("Toggle All Overlays (Ctrl+Alt+H)")
        visibility_action.triggered.connect(self.signals.toggle_visibility.emit)

        debug_action = menu.addAction("Debug: Show Canvas Extent")
        debug_action.triggered.connect(self.signals.debug_canvas_extents.emit)

        menu.addSeparator()

        # ── Sanctuary Mode ──
        sanctuary_menu = menu.addMenu("Sanctuary Mode")

        self._sanctuary_toggle = sanctuary_menu.addAction("Enable Sanctuary")
        self._sanctuary_toggle.setCheckable(True)
        self._sanctuary_toggle.setChecked(
            self.config.get("sanctuary", "enabled") if self.config else False
        )
        self._sanctuary_toggle.triggered.connect(self.signals.sanctuary_toggled.emit)

        sanctuary_menu.addSeparator()

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

        # ── Notifications ──
        modules_menu = menu.addMenu("Notifications")

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

        # ── Integrations ──
        integrations_menu = menu.addMenu("Integrations")

        telegram_action = integrations_menu.addAction("Set Telegram Bot Token...")
        telegram_action.triggered.connect(self._set_telegram_token)

        self._webhook_toggle = integrations_menu.addAction("Enable Webhook Server (port 7277)")
        self._webhook_toggle.setCheckable(True)
        self._webhook_toggle.setChecked(
            self.config.get("webhook", "enabled") if self.config else False
        )
        self._webhook_toggle.triggered.connect(
            lambda checked: self.signals.webhook_toggled.emit(checked)
        )

        integrations_menu.addSeparator()

        llm_menu = integrations_menu.addMenu("LLM Brain")
        anthropic_action = llm_menu.addAction("Set Anthropic API Key...")
        anthropic_action.triggered.connect(
            lambda: self._set_llm_key("anthropic")
        )
        openai_action = llm_menu.addAction("Set OpenAI API Key...")
        openai_action.triggered.connect(
            lambda: self._set_llm_key("openai")
        )

        integrations_menu.addSeparator()
        self._status_action = integrations_menu.addAction("Status: Initializing...")
        self._status_action.setEnabled(False)

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
        
        # Read the specific scale, fallback to global_scale or 1.0
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
            # Reopen the active overlay to apply the new scale parameter
            active_ids = self.overlay_manager.get_active_ids()
            if overlay_id in active_ids:
                self.overlay_manager.close_overlay(overlay_id)
                self.overlay_manager.open_overlay(overlay_id)

    def _set_love_notes_path(self):
        path, ok = QInputDialog.getText(
            None, "Love Notes",
            "Enter path to love notes JSON file:"
        )
        if ok and path:
            self.signals.love_notes_path_set.emit(path)

    def _set_telegram_token(self):
        token, ok = QInputDialog.getText(
            None, "Telegram Bot",
            "Enter your Telegram Bot token (from @BotFather):"
        )
        if ok and token.strip():
            self.signals.telegram_token_set.emit(token.strip())

    def _set_llm_key(self, provider):
        label = "Anthropic" if provider == "anthropic" else "OpenAI"
        key, ok = QInputDialog.getText(
            None, f"{label} API Key",
            f"Enter your {label} API key:"
        )
        if ok and key.strip():
            self.signals.llm_key_set.emit(provider, key.strip())

    def update_sanctuary_toggle(self, enabled):
        self._sanctuary_toggle.setChecked(enabled)

    def update_status(self, text):
        if hasattr(self, '_status_action'):
            self._status_action.setText(f"Status: {text}")
