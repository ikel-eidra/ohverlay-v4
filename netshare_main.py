"""
NetShare — Standalone Network Folder Notification Overlay
=========================================================
Lightweight overlay that monitors your teammates' shared network folders and
shows a floating bubble notification when someone leaves a file for you.
No fish. No AI. Just the notification layer.

Architecture:
  - Transparent PySide6 overlay window (one per monitor)
  - BubbleSystem from Ohverlay for floating text bubbles
  - NetworkFolderWatcher polls peer _ohverlay/ subfolders every 30 s
  - NetworkNotifier writes notify_<recipient>_<ts>.json to your own folder
  - NetShareTray for tray icon, setup dialogs, and "Notify Peer" menu
  - NetShareSettings persists config to ~/.netshare/config.json

Usage:
  python netshare_main.py
  -- or after build --
  NetShare.exe   (runs silently, lives in system tray)
"""

import sys
import os
import signal
import subprocess

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QTimer

from netshare_settings import NetShareSettings
from netshare_overlay import NetShareOverlay
from netshare_tray import NetShareTray
from modules.network_folder_watcher import NetworkFolderWatcher
from modules.network_notifier import NetworkNotifier
from ui.bubbles import BubbleSystem
from utils.logger import logger


class NetShareApp:
    """Wires together all NetShare subsystems."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("NetShare")
        self.app.setOrganizationName("Ohverlay")
        self.app.setQuitOnLastWindowClosed(False)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.config = NetShareSettings()

        self._init_bubbles()
        self._init_overlays()
        self._init_modules()
        self._init_tray()
        self._init_poll_timer()

        # Most-recent pending notification for balloon click handling
        self._last_notification = None

        logger.info("NetShare started.")

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def _init_bubbles(self):
        self.bubble_system = BubbleSystem(config=self.config)
        # Deliver messages immediately (no 60-second rate limit for alerts)
        self.bubble_system.min_interval = 2.0

    def _init_overlays(self):
        """Create one transparent overlay window per connected monitor."""
        screens = QGuiApplication.screens()
        self.overlays = []
        for screen in screens:
            geo = screen.geometry()
            overlay = NetShareOverlay(geo, self.bubble_system)
            overlay.show()
            self.overlays.append(overlay)
        logger.info(f"NetShare overlays created on {len(screens)} monitor(s).")

    def _init_modules(self):
        self.watcher = NetworkFolderWatcher(config=self.config)
        self.notifier = NetworkNotifier(config=self.config)
        self.watcher.on_notification_received = self._on_notification_received

    def _init_tray(self):
        self.tray = NetShareTray(config=self.config)
        self.tray.signals.toggled.connect(self._on_toggled)
        self.tray.signals.notify_peer.connect(self._on_notify_peer)
        self.tray.signals.setup.connect(self._on_setup)
        self.tray.signals.open_log.connect(self._on_open_log)
        self.tray.signals.quit_app.connect(self._on_quit)
        self.tray.messageClicked.connect(self._on_balloon_clicked)
        self.tray.set_peer_names(self.notifier.get_peer_names())
        self.tray.show()

    def _init_poll_timer(self):
        """
        Drive the module polling loop (equivalent to brain._check_modules).
        Runs every 10 seconds — the modules themselves throttle to their own intervals.
        """
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_modules)
        self._poll_timer.start(10_000)

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
                    self._deliver_bubble(msg, category)
            except Exception as e:
                logger.warning(f"[NetShare] Module poll error: {e}")

    def _deliver_bubble(self, message, category="network"):
        """Queue a bubble and force-deliver it immediately on the primary overlay."""
        self.bubble_system.queue_message(message, category)
        if self.overlays:
            self.overlays[0].force_deliver_next()

    # ------------------------------------------------------------------
    # Notification received callback (immediate, from watcher thread)
    # ------------------------------------------------------------------

    def _on_notification_received(self, notification, peer_folder):
        """Show a tray balloon the instant a notification arrives."""
        self._last_notification = notification
        sender = notification.get("sender", "someone")
        filename = notification.get("filename", "").strip()
        if filename:
            title = f"File ready from {sender}"
            body = f"'{filename}' — click to open their folder"
        else:
            msg = notification.get("message", "").strip()
            title = f"Message from {sender}"
            body = msg if msg else "Click to open their shared folder"
        self.tray.showMessage(title, body, self.tray.icon(), 8000)

    def _on_balloon_clicked(self):
        """User clicked the tray balloon — open the sender's folder."""
        if self._last_notification:
            self.watcher.open_sender_folder(self._last_notification)
            self._last_notification = None

    # ------------------------------------------------------------------
    # Tray signal handlers
    # ------------------------------------------------------------------

    def _on_toggled(self, enabled):
        self.watcher.enabled = enabled
        self.notifier.enabled = enabled
        self.config.set("network_sharing", "enabled", enabled)
        self.tray.update_toggle(enabled)
        logger.info(f"NetShare {'enabled' if enabled else 'disabled'}")

    def _on_notify_peer(self, peer_name, filename, message):
        ok = self.notifier.send_notification(peer_name, filename, message)
        if ok:
            self._deliver_bubble(
                f"\U0001f4e4 Notified {peer_name}" + (f": {filename}" if filename else ""),
                "network",
            )
        else:
            self.tray.showMessage(
                "NetShare",
                "Could not send notification — check your shared folder config.",
                self.tray.icon(),
                5000,
            )

    def _on_setup(self, my_folder, my_username, peers):
        self.config.set("network_sharing", "my_folder", my_folder)
        self.config.set("network_sharing", "my_username", my_username)
        self.config.set("network_sharing", "peers", peers)
        self.config.set("network_sharing", "enabled", True)

        self.watcher.my_folder = my_folder
        self.watcher.my_username = my_username.lower().strip()
        self.watcher.peers = peers
        self.watcher.enabled = True

        self.notifier.my_folder = my_folder
        self.notifier.my_username = my_username.lower().strip()
        self.notifier.peers = peers
        self.notifier.enabled = True

        self.tray.set_peer_names(self.notifier.get_peer_names())
        self.tray.update_toggle(True)
        self._deliver_bubble(f"\U0001f4c1 NetShare ready for {my_username}", "network")
        logger.info(f"NetShare configured: folder={my_folder}, user={my_username}, peers={peers}")

    def _on_open_log(self):
        log_path = self.watcher.log_path
        if os.path.exists(log_path):
            try:
                subprocess.Popen(["notepad", log_path])
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
        logger.info("NetShare exiting.")
        self.app.quit()

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    NetShareApp().run()
