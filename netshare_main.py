"""
NetShare — Standalone Network Folder Notification Overlay
=========================================================
Developed by:  Futol Ethical Technology Ecosystems
Deployed for:  Sarah Attaqnia Contracting Company

Monitors teammates' shared network folders. When a colleague drops a file
for you and clicks "Notify", a glowing post-it card slides in on your screen.
Click the card to open their folder. All activity is logged and viewable
in the engineering console.

Architecture:
  NetShareApp
    ├── NetShareCardManager  — glowing post-it notification cards
    ├── NetShareConsole      — engineering professional activity log window
    ├── NetShareTray         — system tray icon + menus
    ├── NetworkFolderWatcher — polls peers' _ohverlay/ subfolders (30 s)
    ├── NetworkNotifier      — writes notifications + polls for ack confirmations
    └── NetShareSettings     — config at %USERPROFILE%\\.netshare\\config.json

Usage:
  python netshare_main.py
  -- or after build --
  NetShare.exe  (lives silently in the system tray)
"""

import sys
import os
import signal
import subprocess

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from netshare_settings import NetShareSettings
from netshare_overlay import NetShareCardManager
from netshare_tray import NetShareTray
from netshare_console import NetShareConsole
from modules.network_folder_watcher import NetworkFolderWatcher
from modules.network_notifier import NetworkNotifier
from utils.logger import logger


class NetShareApp:
    """
    Top-level application controller.
    Wires together all NetShare subsystems and drives the polling loop.
    """

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("NetShare")
        self.app.setApplicationDisplayName(
            "NetShare · Futol Ethical Technology Ecosystems"
        )
        self.app.setOrganizationName("Futol Ethical Technology Ecosystems")
        self.app.setQuitOnLastWindowClosed(False)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.config = NetShareSettings()

        self._init_modules()
        self._init_cards()
        self._init_console()
        self._init_tray()
        self._init_poll_timer()

        # Most-recent incoming notification for tray-balloon click
        self._last_notification = None

        logger.info("NetShare started — Futol Ethical Technology Ecosystems")
        logger.info("Client: Sarah Attaqnia Contracting Company")

    # ------------------------------------------------------------------
    # Init helpers
    # ------------------------------------------------------------------

    def _init_modules(self):
        self.watcher  = NetworkFolderWatcher(config=self.config)
        self.notifier = NetworkNotifier(config=self.config)
        self.watcher.on_notification_received = self._on_notification_received

    def _init_cards(self):
        self.card_manager = NetShareCardManager(
            on_open_folder_cb=self._on_open_folder
        )

    def _init_console(self):
        self.console = NetShareConsole(log_path=self.watcher.log_path)
        self.console.closed.connect(self._on_console_closed)
        self._console_visible = False
        # Sync initial peer status
        self._refresh_peer_status()

    def _init_tray(self):
        self.tray = NetShareTray(config=self.config)
        self.tray.signals.toggled.connect(self._on_toggled)
        self.tray.signals.notify_peer.connect(self._on_notify_peer)
        self.tray.signals.setup.connect(self._on_setup)
        self.tray.signals.open_console.connect(self._on_open_console)
        self.tray.signals.open_log.connect(self._on_open_log)
        self.tray.signals.quit_app.connect(self._on_quit)
        self.tray.messageClicked.connect(self._on_balloon_clicked)
        self.tray.set_peer_names(self.notifier.get_peer_names())
        self.tray.show()

    def _init_poll_timer(self):
        """Poll modules every 10 s; modules self-throttle to their own intervals."""
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_modules)
        self._poll_timer.start(10_000)

        # Peer reachability check every 60 s
        self._peer_timer = QTimer()
        self._peer_timer.timeout.connect(self._refresh_peer_status)
        self._peer_timer.start(60_000)

    # ------------------------------------------------------------------
    # Module polling
    # ------------------------------------------------------------------

    def _poll_modules(self):
        for module in (self.watcher, self.notifier):
            if not module.enabled:
                continue
            try:
                messages = module.check()
                for msg, category in messages:
                    # Ack confirmations from notifier → show as card too
                    if category == "network" and msg.startswith("\u2705"):
                        self._show_ack_card(msg)
            except Exception as e:
                logger.warning(f"[NetShare] Poll error: {e}")

    def _show_ack_card(self, message):
        """Show a minimal 'delivery confirmed' notification card."""
        pseudo_notif = {
            "sender":   "SYSTEM",
            "filename": message,
            "message":  "",
            "timestamp": "",
        }
        self.card_manager.show_notification(pseudo_notif)

    # ------------------------------------------------------------------
    # Notification received (immediate, called by watcher callback)
    # ------------------------------------------------------------------

    def _on_notification_received(self, notification, peer_folder):
        """
        Fires the moment NetworkFolderWatcher spots a new notify file.
        Spawns a glowing card AND a tray balloon.
        """
        self._last_notification = notification
        self.card_manager.show_notification(notification)

        # Tray balloon (for users who may have minimised their screen)
        sender   = notification.get("sender", "someone")
        filename = notification.get("filename", "").strip()
        title = f"📁  File ready from {sender}"
        body  = f"'{filename}' — click card or balloon to open" if filename \
                else (notification.get("message", "") or "Click to open their folder")
        self.tray.showMessage(title, body, self.tray.icon(), 8000)

        # Refresh console log
        if self._console_visible:
            self.console._load_log()

    def _on_balloon_clicked(self):
        """Tray balloon clicked — open the sender's folder and write ack."""
        if self._last_notification:
            self.watcher.open_sender_folder(self._last_notification)
            self._last_notification = None
            if self._console_visible:
                self.console._load_log()

    def _on_open_folder(self, notification):
        """Card 'Open Folder' button clicked — write ack."""
        self.watcher.write_ack(notification, action="opened")
        self._last_notification = None
        if self._console_visible:
            self.console._load_log()

    # ------------------------------------------------------------------
    # Tray signal handlers
    # ------------------------------------------------------------------

    def _on_toggled(self, enabled):
        self.watcher.enabled  = enabled
        self.notifier.enabled = enabled
        self.config.set("network_sharing", "enabled", enabled)
        self.tray.update_toggle(enabled)
        logger.info(f"NetShare {'enabled' if enabled else 'disabled'}")

    def _on_notify_peer(self, peer_name, filename, message):
        ok = self.notifier.send_notification(peer_name, filename, message)
        if ok:
            # Confirm card for the sender
            self.card_manager.show_notification({
                "sender":    "YOU → " + peer_name.upper(),
                "filename":  filename,
                "message":   message or "Notification sent",
                "timestamp": "",
            })
        else:
            self.tray.showMessage(
                "NetShare — Error",
                "Could not send notification.\n"
                "Check your shared folder path in Configure.",
                self.tray.icon(),
                5000,
            )
        if self._console_visible:
            self.console._load_log()

    def _on_setup(self, my_folder, my_username, peers):
        self.config.set("network_sharing", "my_folder",    my_folder)
        self.config.set("network_sharing", "my_username",  my_username)
        self.config.set("network_sharing", "peers",        peers)
        self.config.set("network_sharing", "enabled",      True)

        for mod in (self.watcher, self.notifier):
            mod.my_folder   = my_folder
            mod.my_username = my_username.lower().strip()
            mod.peers       = peers
            mod.enabled     = True

        self.tray.set_peer_names(self.notifier.get_peer_names())
        self.tray.update_toggle(True)
        self._refresh_peer_status()

        self.card_manager.show_notification({
            "sender":    "SYSTEM",
            "filename":  f"Configured as  {my_username}",
            "message":   f"Watching {len(peers)} peer(s)",
            "timestamp": "",
        })
        logger.info(f"Setup: folder={my_folder}, user={my_username}, peers={peers}")

    def _on_open_console(self):
        if not self._console_visible:
            # Re-create console if it was closed
            if not self.console.isVisible():
                self.console = NetShareConsole(log_path=self.watcher.log_path)
                self.console.closed.connect(self._on_console_closed)
                self._refresh_peer_status()
            self.console.show()
            self.console.raise_()
            self.console.activateWindow()
            self.console._load_log()
            self._console_visible = True
        else:
            self.console.raise_()
            self.console.activateWindow()

    def _on_console_closed(self):
        self._console_visible = False

    def _on_open_log(self):
        log = self.watcher.log_path
        if os.path.exists(log):
            try:
                subprocess.Popen(["notepad", log])
            except Exception:
                pass
        else:
            self.tray.showMessage(
                "NetShare Log",
                "No activity yet. Log appears after the first notification.",
                self.tray.icon(),
                4000,
            )

    def _on_quit(self):
        logger.info("NetShare shutting down.")
        self.app.quit()

    # ------------------------------------------------------------------
    # Peer reachability check (quick folder access test)
    # ------------------------------------------------------------------

    def _refresh_peer_status(self):
        peers_status = []
        for peer in self.watcher.peers:
            name   = peer.get("name", "")
            folder = peer.get("folder", "")
            reachable = bool(folder and os.path.isdir(folder))
            peers_status.append((name, reachable))
        if hasattr(self, "console"):
            self.console.update_peers(peers_status)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    NetShareApp().run()
