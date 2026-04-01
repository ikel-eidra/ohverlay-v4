"""
Network Notifier - Send file-ready notifications to peers via your own shared folder.

The sender writes notify_<recipient>_<timestamp>.json into their OWN _ohverlay/
subfolder. The sender's Ohverlay also polls each peer's _ohverlay/ folder for ack
files confirming the recipient has opened/copied the file.

This module runs alongside NetworkFolderWatcher. Both are registered with the
brain so their .check() methods are called on the polling loop.
"""

import json
import os
import time
import uuid
from datetime import datetime
from utils.logger import logger


SUBFOLDER = "_ohverlay"


class NetworkNotifier:
    """
    Writes notification files to your own shared folder so peers can see them.
    Polls peer folders for acknowledgement files confirming delivery.
    """

    def __init__(self, config=None):
        self.enabled = False
        self.my_folder = ""
        self.my_username = ""
        self.peers = []
        self.log_path = os.path.join(
            os.path.expanduser("~"), ".zenfish", "net_share_log.jsonl"
        )

        # id -> {"notification": {...}, "acked": bool}
        self._sent_notifications = {}
        self._seen_ack_ids = set()     # notification_ids already confirmed
        self._last_ack_check = 0
        self._ack_check_interval = 60  # seconds between ack polls

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
        custom_log = cfg.get("log_path", "")
        if custom_log:
            self.log_path = custom_log

    # ------------------------------------------------------------------
    # Public API: called from tray "Notify Peer" menu
    # ------------------------------------------------------------------

    def send_notification(self, recipient_name, filename="", message=""):
        """
        Write a notification JSON file to our own _ohverlay/ subfolder.
        The recipient's Ohverlay will detect it during the next poll cycle.

        Returns True on success, False on failure.
        """
        if not self.my_folder:
            logger.warning("[NetworkNotifier] my_folder not configured.")
            return False
        if not self.my_username:
            logger.warning("[NetworkNotifier] my_username not configured.")
            return False

        ohverlay_dir = os.path.join(self.my_folder, SUBFOLDER)
        try:
            os.makedirs(ohverlay_dir, exist_ok=True)
        except OSError as e:
            logger.warning(f"[NetworkNotifier] Cannot create _ohverlay dir: {e}")
            return False

        recipient = recipient_name.lower().strip()
        notif_id = str(uuid.uuid4())[:8]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        notify_path = os.path.join(ohverlay_dir, f"notify_{recipient}_{ts}.json")

        notification = {
            "type": "notification",
            "id": notif_id,
            "sender": self.my_username,
            "recipient": recipient,
            "filename": filename.strip(),
            "message": message.strip(),
            "timestamp": datetime.now().isoformat(),
            "sender_folder": self.my_folder,
        }
        try:
            with open(notify_path, "w", encoding="utf-8") as f:
                json.dump(notification, f, indent=2)
            self._sent_notifications[notif_id] = {
                "notification": notification,
                "acked": False,
            }
            self._log_event(
                "sent",
                to=recipient,
                filename=filename,
                notification_id=notif_id,
            )
            logger.info(
                f"[NetworkNotifier] Notification sent to {recipient} "
                f"(file='{filename}', id={notif_id})"
            )
            return True
        except IOError as e:
            logger.warning(f"[NetworkNotifier] Could not write notification: {e}")
            return False

    def get_peer_names(self):
        """Return list of configured peer display names."""
        return [p.get("name", "") for p in self.peers if p.get("name")]

    def get_peer_by_name(self, name):
        """Return peer dict matching name (case-insensitive), or None."""
        name_lower = name.lower().strip()
        for peer in self.peers:
            if peer.get("name", "").lower().strip() == name_lower:
                return peer
        return None

    # ------------------------------------------------------------------
    # Brain module interface: poll for acks
    # ------------------------------------------------------------------

    def check(self):
        """
        Called by the brain's polling loop every ~10 seconds.
        Polls each peer's _ohverlay/ folder for ack files addressed to us.
        Returns [(message_text, "network")] tuples for confirmed deliveries.
        """
        if not self.enabled or not self.peers or not self.my_username:
            return []

        now = time.time()
        if now - self._last_ack_check < self._ack_check_interval:
            return []
        self._last_ack_check = now

        messages = []
        for peer in self.peers:
            peer_name = peer.get("name", "").strip()
            peer_folder = peer.get("folder", "").strip()
            if not peer_name or not peer_folder:
                continue
            try:
                found = self._scan_peer_acks(peer_name, peer_folder)
                messages.extend(found)
            except Exception as e:
                logger.warning(
                    f"[NetworkNotifier] Error checking acks from {peer_name}: {e}"
                )

        return messages

    # ------------------------------------------------------------------
    # Internal ack scanning
    # ------------------------------------------------------------------

    def _scan_peer_acks(self, peer_name, peer_folder):
        """Check peer's _ohverlay/ folder for ack files addressed to us."""
        ohverlay_dir = os.path.join(peer_folder, SUBFOLDER)
        if not os.path.isdir(ohverlay_dir):
            return []

        prefix = f"ack_to_{self.my_username}_"
        try:
            entries = os.listdir(ohverlay_dir)
        except PermissionError:
            return []

        messages = []
        for filename in sorted(entries):
            if not filename.startswith(prefix) or not filename.endswith(".json"):
                continue

            filepath = os.path.join(ohverlay_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    ack = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            notif_id = ack.get("notification_id", "")
            # Deduplicate: skip if we already processed this ack
            ack_key = f"{notif_id}:{ack.get('action', 'opened')}"
            if ack_key in self._seen_ack_ids:
                continue
            self._seen_ack_ids.add(ack_key)

            action = ack.get("action", "received")
            from_user = ack.get("from", peer_name)

            if notif_id in self._sent_notifications:
                sent = self._sent_notifications[notif_id]
                sent["acked"] = True
                fname = sent["notification"].get("filename", "")
                if fname:
                    bubble = f"\u2705 {from_user} {action} your file: {fname}"
                else:
                    bubble = f"\u2705 {from_user} {action} your notification"
                if len(bubble) > 80:
                    bubble = bubble[:77] + "..."
                messages.append((bubble, "network"))
                self._log_event(
                    "ack_received",
                    from_user=from_user,
                    notification_id=notif_id,
                    action=action,
                )
                logger.info(
                    f"[NetworkNotifier] Ack from {from_user}: {action} "
                    f"(notification_id={notif_id})"
                )

        return messages

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
