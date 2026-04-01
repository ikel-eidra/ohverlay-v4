"""
NetShare System Tray — engineering-themed tray icon for the standalone app.

Branding: Futol Ethical Technology Ecosystems
Client:   Sarah Attaqnia Contracting Company
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QInputDialog
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QRadialGradient, QPen, QFont
from PySide6.QtCore import Qt, Signal, QObject, QPoint


class NetShareTraySignals(QObject):
    notify_peer  = Signal(str, str, str)   # peer_name, filename, message
    setup        = Signal(str, str, list)  # my_folder, my_username, peers
    open_console = Signal()
    open_log     = Signal()
    toggled      = Signal(bool)
    quit_app     = Signal()


class NetShareTray(QSystemTrayIcon):
    """Minimal, engineering-professional system tray for NetShare."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.signals = NetShareTraySignals()
        self.config = config

        self._enabled    = False
        self._peer_names = []

        if config:
            net = config.get("network_sharing")
            if isinstance(net, dict):
                self._enabled    = net.get("enabled", False)
                self._peer_names = [
                    p.get("name", "") for p in net.get("peers", []) if p.get("name")
                ]

        self._create_icon()
        self._create_menu()
        self.setToolTip(
            "NetShare  ·  Futol Ethical Technology Ecosystems\n"
            "Sarah Attaqnia Contracting Company"
        )

    # ------------------------------------------------------------------
    # Icon — folder with a glowing cyan notification dot
    # ------------------------------------------------------------------

    def _create_icon(self):
        px = QPixmap(32, 32)
        px.fill(Qt.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)

        # Folder body gradient (dark navy → steel)
        grad = QRadialGradient(QPoint(13, 18), 14)
        grad.setColorAt(0.0, QColor(20,  80, 140, 230))
        grad.setColorAt(1.0, QColor(8,   30,  60, 210))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(0, 160, 210, 180), 1))
        p.drawRoundedRect(3, 11, 22, 16, 3, 3)   # folder body
        p.drawRoundedRect(3,  7, 10,  6, 2, 2)   # folder tab

        # Notification dot (cyan, glowing)
        p.setBrush(QBrush(QColor(0, 220, 255, 240)))
        p.setPen(QPen(QColor(0, 140, 200, 180), 1))
        p.drawEllipse(20, 4, 10, 10)
        # Inner highlight
        p.setBrush(QBrush(QColor(255, 255, 255, 130)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(22, 5, 4, 4)

        p.end()
        self.setIcon(QIcon(px))

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: #080F18;
                color: #C8E8FF;
                border: 1px solid #0D2840;
                font-family: Segoe UI;
                font-size: 9pt;
            }
            QMenu::item:selected {
                background: #006880;
                color: #E8F8FF;
            }
            QMenu::separator {
                height: 1px;
                background: #0D2840;
                margin: 3px 8px;
            }
            QMenu::item:disabled {
                color: #3A6080;
            }
        """)

        # Header (non-interactive branding)
        hdr = menu.addAction("📁  NetShare  ·  v1.0")
        hdr.setEnabled(False)
        sub = menu.addAction("     Sarah Attaqnia Contracting Company")
        sub.setEnabled(False)
        menu.addSeparator()

        # Enable toggle
        self._toggle = menu.addAction("Enable Notifications")
        self._toggle.setCheckable(True)
        self._toggle.setChecked(self._enabled)
        self._toggle.triggered.connect(lambda checked: self.signals.toggled.emit(checked))

        menu.addSeparator()

        # Notify a peer
        self._notify_menu = menu.addMenu("🔔  Notify a Peer")
        self._notify_menu.setStyleSheet(menu.styleSheet())
        self._rebuild_notify_menu()

        # Configure
        cfg_action = menu.addAction("⚙  Configure My Shared Folder...")
        cfg_action.triggered.connect(self._configure_sharing)

        menu.addSeparator()

        # Console + Log
        console_action = menu.addAction("📊  Open Activity Console")
        console_action.triggered.connect(self.signals.open_console.emit)

        log_action = menu.addAction("📄  Open Raw Log (Notepad)")
        log_action.triggered.connect(self.signals.open_log.emit)

        menu.addSeparator()

        # Quit
        quit_action = menu.addAction("✕  Quit NetShare")
        quit_action.triggered.connect(self.signals.quit_app.emit)

        self.setContextMenu(menu)

    # ------------------------------------------------------------------
    # Notify peer submenu
    # ------------------------------------------------------------------

    def _rebuild_notify_menu(self):
        self._notify_menu.clear()
        if not self._peer_names:
            ph = self._notify_menu.addAction("(No peers configured yet)")
            ph.setEnabled(False)
            return
        for name in self._peer_names:
            action = self._notify_menu.addAction(name)
            action.triggered.connect(
                lambda checked, pn=name: self._notify_dialog(pn)
            )

    def _notify_dialog(self, peer_name):
        filename, ok1 = QInputDialog.getText(
            None,
            "NetShare — Notify Peer",
            f"File or folder name you're sharing with  {peer_name}:\n"
            "(leave blank to send a plain message)"
        )
        if not ok1:
            return
        message, ok2 = QInputDialog.getText(
            None,
            "NetShare — Notify Peer",
            f"Optional message to  {peer_name}:"
        )
        if not ok2:
            return
        self.signals.notify_peer.emit(peer_name, filename.strip(), message.strip())

    # ------------------------------------------------------------------
    # Setup dialog
    # ------------------------------------------------------------------

    def _configure_sharing(self):
        my_folder, ok1 = QInputDialog.getText(
            None,
            "NetShare Setup — Step 1 of 3",
            "Your shared folder path on the network:\n\n"
            "Example:  \\\\server\\shared\\yourname\n"
            "(This is YOUR folder — others can read from it but not write to it)"
        )
        if not ok1 or not my_folder.strip():
            return

        my_username, ok2 = QInputDialog.getText(
            None,
            "NetShare Setup — Step 2 of 3",
            "Your display name on this network:\n\n"
            "(Peers will see this name when you notify them)"
        )
        if not ok2 or not my_username.strip():
            return

        peers_raw, ok3 = QInputDialog.getText(
            None,
            "NetShare Setup — Step 3 of 3",
            "Enter your peers, one per line,  name = \\\\path :\n\n"
            "Example:\n"
            "  maria = \\\\server\\shared\\maria\n"
            "  ben   = \\\\server\\shared\\ben\n\n"
            "(You can edit ~/.netshare/config.json later to add more)"
        )
        if not ok3:
            return

        peers = []
        for line in peers_raw.strip().splitlines():
            if "=" in line:
                parts = line.split("=", 1)
                nm = parts[0].strip()
                fp = parts[1].strip()
                if nm and fp:
                    peers.append({"name": nm, "folder": fp})

        self.signals.setup.emit(my_folder.strip(), my_username.strip(), peers)

    # ------------------------------------------------------------------
    # Public state sync
    # ------------------------------------------------------------------

    def set_peer_names(self, names):
        self._peer_names = [n for n in names if n]
        self._rebuild_notify_menu()

    def update_toggle(self, enabled):
        self._toggle.setChecked(enabled)
