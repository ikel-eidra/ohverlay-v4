"""
Network Folder Watcher - Real-time file drop notifications for shared network folders.

How it works (respects read-only network permissions):
- Each user has their own shared folder on the network (e.g. \\\\server\\shared\\john\\)
- Others can only READ from your folder; they cannot write to it
- To notify a recipient, the SENDER writes a small JSON file into their OWN folder's
  _ohverlay/ subfolder: notify_<recipient>_<timestamp>.json
- The RECIPIENT's Ohverlay polls all peer _ohverlay/ subfolders for files addressed to them
- When the recipient opens the sender's folder, Ohverlay writes an ack to THEIR OWN
  folder's _ohverlay/ subfolder so the sender can confirm delivery
- All activity is logged locally at ~/.zenfish/net_share_log.jsonl on each machine

Directory layout on the network share:
  \\\\server\\shared\\john\\
      _ohverlay\\
          notify_maria_20260401_120000.json   <- John is notifying Maria
          ack_to_john_20260401_120500.json    <- Maria confirmed (written by Maria's machine)
      my_report.pdf
      for_maria\\
          ...
"""

import json
import os
import time
from datetime import datetime
from utils.logger import logger


SUBFOLDER = "_ohverlay"


class NetworkFolderWatcher:
    """
    Polls peer shared folders for notification files addressed to this user.
    Integrates with the brain's module polling system via .check().

    The brain calls .check() every ~10 seconds; this module throttles to
    check_interval_seconds (default 30s) to avoid hammering the network.
    """

    def __init__(self, config=None):
        self.enabled = False
        self.my_folder = ""        # e.g. \\\\server\\shared\\john
        self.my_username = ""      # e.g. "john"
        self.peers = []            # [{"name": "maria", "folder": "\\\\server\\shared\\maria"}, ...]
        self.check_interval = 30   # seconds between network polls
        self.log_path = os.path.join(
            os.path.expanduser("~"), ".zenfish", "net_share_log.jsonl"
        )

        self._last_check = 0
        self._seen_notification_ids = set()
        self._pending_notifications = []  # Received but not yet opened by user

        # Set by main.py to trigger a tray balloon + store last notification for click
        self.on_notification_received = None  # callable(notification_dict, peer_folder)

        if config:
            self._load_config(config)

    def _load_config(self, config):
        cfg = config.get("network_sharing") if hasattr(config, "get") else {}
        if not isinstance(cfg, dict):
            return
        self.enabled = cfg.get("enabled", False)
        self.my_folder = cfg.get("my_folder", "")
        self.my_username = cfg.get("my_username", "").lower().strip()
        self.peers = cfg.get("peers", [])
        self.check_interval = cfg.get("check_interval_seconds", 30)
        custom_log = cfg.get("log_path", "")
        if custom_log:
            self.log_path = custom_log

    # ------------------------------------------------------------------
    # Brain module interface
    # ------------------------------------------------------------------

    def check(self):
        """
        Called by the brain's polling loop every ~10 seconds.
        Returns a list of (message_text, category) tuples to display as bubbles.
        Throttled to check_interval_seconds to reduce network I/O.
        """
        if not self.enabled or not self.my_username or not self.peers:
            return []

        now = time.time()
        if now - self._last_check < self.check_interval:
            return []
        self._last_check = now

        messages = []
        for peer in self.peers:
            peer_name = peer.get("name", "").strip()
            peer_folder = peer.get("folder", "").strip()
            if not peer_name or not peer_folder:
                continue
            try:
                found = self._scan_peer_folder(peer_name, peer_folder)
                messages.extend(found)
            except Exception as e:
                logger.warning(f"[NetworkFolderWatcher] Error checking {peer_name}: {e}")

        return messages

    # ------------------------------------------------------------------
    # Internal scanning
    # ------------------------------------------------------------------

    def _scan_peer_folder(self, peer_name, peer_folder):
        """Scan peer's _ohverlay/ subfolder for notification files addressed to me."""
        ohverlay_dir = os.path.join(peer_folder, SUBFOLDER)
        if not os.path.isdir(ohverlay_dir):
            return []

        prefix = f"notify_{self.my_username}_"
        try:
            entries = os.listdir(ohverlay_dir)
        except PermissionError:
            logger.warning(f"[NetworkFolderWatcher] No read access to {ohverlay_dir}")
            return []

        messages = []
        for filename in sorted(entries):  # sorted = chronological order by timestamp in name
            if not filename.startswith(prefix) or not filename.endswith(".json"):
                continue

            filepath = os.path.join(ohverlay_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    notif = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"[NetworkFolderWatcher] Unreadable file {filepath}: {e}")
                continue

            notif_id = notif.get("id") or filepath
            if notif_id in self._seen_notification_ids:
                continue
            self._seen_notification_ids.add(notif_id)

            # Enrich with routing info for later open/ack
            notif["_peer_folder"] = peer_folder
            notif["_peer_name"] = peer_name

            sender = notif.get("sender", peer_name)
            file_info = notif.get("filename", "").strip()
            custom_msg = notif.get("message", "").strip()

            if file_info:
                bubble = f"\U0001f4c1 {sender}: \u2018{file_info}\u2019 is ready for you"
            elif custom_msg:
                bubble = f"\U0001f4c1 {sender}: {custom_msg}"
            else:
                bubble = f"\U0001f4c1 {sender} left a file for you"

            if len(bubble) > 80:
                bubble = bubble[:77] + "..."

            self._pending_notifications.append(notif)
            self._log_event(
                "received",
                sender=sender,
                filename=file_info,
                notification_id=notif_id,
            )
            logger.info(f"[NetworkFolderWatcher] New notification from {sender}: {file_info or custom_msg}")
            messages.append((bubble, "network"))

            if self.on_notification_received:
                try:
                    self.on_notification_received(notif, peer_folder)
                except Exception as cb_err:
                    logger.warning(f"[NetworkFolderWatcher] Callback error: {cb_err}")

        return messages

    # ------------------------------------------------------------------
    # Ack writing (called when user opens the sender's folder)
    # ------------------------------------------------------------------

    def write_ack(self, notification, action="opened"):
        """
        Write an ack file into OUR OWN folder's _ohverlay/ subfolder.
        The sender's Ohverlay polls this to confirm delivery.
        action: "received" | "opened"
        """
        if not self.my_folder:
            logger.warning("[NetworkFolderWatcher] my_folder not configured; cannot write ack.")
            return

        ohverlay_dir = os.path.join(self.my_folder, SUBFOLDER)
        try:
            os.makedirs(ohverlay_dir, exist_ok=True)
        except OSError as e:
            logger.warning(f"[NetworkFolderWatcher] Cannot create own _ohverlay dir: {e}")
            return

        sender = notification.get("sender", "unknown")
        notif_id = notification.get("id", "unknown")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ack_path = os.path.join(ohverlay_dir, f"ack_to_{sender}_{ts}.json")

        ack = {
            "type": "ack",
            "from": self.my_username,
            "to": sender,
            "notification_id": notif_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            with open(ack_path, "w", encoding="utf-8") as f:
                json.dump(ack, f, indent=2)
            self._log_event(action, sender=sender, notification_id=notif_id)
            logger.info(f"[NetworkFolderWatcher] Ack written for {sender} (action={action})")
        except IOError as e:
            logger.warning(f"[NetworkFolderWatcher] Could not write ack: {e}")

    # ------------------------------------------------------------------
    # Open folder helper
    # ------------------------------------------------------------------

    def open_sender_folder(self, notification):
        """
        Open the sender's shared folder in Windows Explorer and write an ack.
        Removes the notification from pending list.
        """
        peer_folder = notification.get("_peer_folder") or notification.get("sender_folder", "")
        if peer_folder and os.path.isdir(peer_folder):
            try:
                import subprocess
                subprocess.Popen(["explorer", os.path.normpath(peer_folder)])
                logger.info(f"[NetworkFolderWatcher] Opened folder: {peer_folder}")
            except Exception as e:
                logger.warning(f"[NetworkFolderWatcher] Could not open folder in Explorer: {e}")
        else:
            logger.warning(f"[NetworkFolderWatcher] Folder not reachable: {peer_folder}")

        self.write_ack(notification, action="opened")

        notif_id = notification.get("id")
        self._pending_notifications = [
            n for n in self._pending_notifications if n.get("id") != notif_id
        ]

    # ------------------------------------------------------------------
    # Pending notifications accessors
    # ------------------------------------------------------------------

    def get_pending_notifications(self):
        return list(self._pending_notifications)

    def has_pending(self):
        return bool(self._pending_notifications)

    def pop_latest_pending(self):
        """Return and remove the most recent pending notification, or None."""
        if self._pending_notifications:
            return self._pending_notifications.pop()
        return None

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_event(self, event, **kwargs):
        """Append a JSONL entry to the local activity log (non-critical)."""
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            entry = {"event": event, "timestamp": datetime.now().isoformat(), **kwargs}
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError:
            pass
