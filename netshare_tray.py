"""
NetShare System Tray — simplified tray icon for the standalone network
notification app. No fish/creature controls. Network Share menu only.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QInputDialog, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QRadialGradient, QBrush
from PySide6.QtCore import Qt, Signal, QObject


class NetShareTraySignals(QObject):
    notify_peer = Signal(str, str, str)   # peer_name, filename, message
    setup = Signal(str, str, list)        # my_folder, my_username, peers
    open_log = Signal()
    toggled = Signal(bool)
    quit_app = Signal()


class NetShareTray(QSystemTrayIcon):
    """Minimal system tray for the standalone NetShare overlay."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.signals = NetShareTraySignals()
        self.config = config

        self._enabled = False
        self._peer_names = []

        if config:
            net_cfg = config.get("network_sharing")
            if isinstance(net_cfg, dict):
                self._enabled = net_cfg.get("enabled", False)
                self._peer_names = [
                    p.get("name", "") for p in net_cfg.get("peers", []) if p.get("name")
                ]

        self._create_icon()
        self._create_menu()
        self.setToolTip("NetShare Notifications")

    # ------------------------------------------------------------------
    # Icon
    # ------------------------------------------------------------------

    def _create_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Folder icon shape
        grad = QRadialGradient(16, 16, 14)
        grad.setColorAt(0.0, QColor(80, 180, 255, 230))
        grad.setColorAt(1.0, QColor(30, 100, 200, 200))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        # Folder body
        painter.drawRoundedRect(4, 12, 24, 16, 3, 3)
        # Folder tab
        painter.drawRoundedRect(4, 8, 10, 6, 2, 2)
        # Notification dot
        painter.setBrush(QColor(255, 80, 80, 230))
        painter.drawEllipse(20, 6, 8, 8)

        painter.end()
        self.setIcon(QIcon(pixmap))

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _create_menu(self):
        menu = QMenu()

        header = menu.addAction("📁 NetShare Notifications v1.0")
        header.setEnabled(False)
        menu.addSeparator()

        self._toggle_action = menu.addAction("Enable Notifications")
        self._toggle_action.setCheckable(True)
        self._toggle_action.setChecked(self._enabled)
        self._toggle_action.triggered.connect(
            lambda checked: self.signals.toggled.emit(checked)
        )

        menu.addSeparator()

        self._notify_menu = menu.addMenu("Notify a Peer")
        self._rebuild_notify_menu()

        setup_action = menu.addAction("Configure My Shared Folder...")
        setup_action.triggered.connect(self._configure_sharing)

        menu.addSeparator()

        log_action = menu.addAction("View Activity Log...")
        log_action.triggered.connect(self.signals.open_log.emit)

        menu.addSeparator()

        quit_action = menu.addAction("Quit NetShare")
        quit_action.triggered.connect(self.signals.quit_app.emit)

        self.setContextMenu(menu)

    def _rebuild_notify_menu(self):
        self._notify_menu.clear()
        if not self._peer_names:
            placeholder = self._notify_menu.addAction("(No peers configured yet)")
            placeholder.setEnabled(False)
            return
        for peer_name in self._peer_names:
            action = self._notify_menu.addAction(peer_name)
            action.triggered.connect(
                lambda checked, pn=peer_name: self._notify_dialog(pn)
            )

    def _notify_dialog(self, peer_name):
        filename, ok1 = QInputDialog.getText(
            None,
            "Notify Peer",
            f"File or folder name you're sharing with {peer_name}:\n"
            "(leave blank to send a plain message)",
        )
        if not ok1:
            return
        message, ok2 = QInputDialog.getText(
            None,
            "Notify Peer",
            f"Optional message to {peer_name}:",
        )
        if not ok2:
            return
        self.signals.notify_peer.emit(peer_name, filename.strip(), message.strip())

    def _configure_sharing(self):
        my_folder, ok1 = QInputDialog.getText(
            None,
            "NetShare Setup",
            "Your shared folder path on the network\n"
            "Example: \\\\server\\shared\\yourname",
        )
        if not ok1 or not my_folder.strip():
            return

        my_username, ok2 = QInputDialog.getText(
            None,
            "NetShare Setup",
            "Your username (peers will see this name when you notify them):",
        )
        if not ok2 or not my_username.strip():
            return

        peers_raw, ok3 = QInputDialog.getText(
            None,
            "NetShare Setup",
            "Peer list — one per line as  name=\\\\path\n"
            "Example:\n"
            "  maria=\\\\server\\shared\\maria\n"
            "  ben=\\\\server\\shared\\ben",
        )
        if not ok3:
            return

        peers = []
        for line in peers_raw.strip().splitlines():
            if "=" in line:
                parts = line.split("=", 1)
                name = parts[0].strip()
                folder = parts[1].strip()
                if name and folder:
                    peers.append({"name": name, "folder": folder})

        self.signals.setup.emit(my_folder.strip(), my_username.strip(), peers)

    # ------------------------------------------------------------------
    # State sync
    # ------------------------------------------------------------------

    def set_peer_names(self, names):
        self._peer_names = [n for n in names if n]
        self._rebuild_notify_menu()

    def update_toggle(self, enabled):
        self._toggle_action.setChecked(enabled)
