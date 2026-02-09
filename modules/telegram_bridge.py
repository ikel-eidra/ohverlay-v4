"""
Telegram Bot bridge for real-time love notes.
Partner sends a message to your Telegram bot -> fish delivers it as a bubble.
Uses long-polling (no webhook server needed) for simplicity and privacy.
"""

import threading
import time
import json
from collections import deque
from utils.logger import logger

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class TelegramBridge:
    """
    Connects to a Telegram Bot for real-time message delivery.

    Setup:
    1. Message @BotFather on Telegram, create a bot, get the token
    2. Set the token in ZenFish config
    3. Your partner messages the bot -> fish delivers it
    """

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, config=None):
        self.enabled = False
        self.token = ""
        self.allowed_users = []  # List of Telegram user IDs allowed to send notes
        self._last_update_id = 0
        self._messages = deque(maxlen=100)
        self._poll_thread = None
        self._running = False
        self._poll_interval = 3  # seconds

        if config:
            self._load_config(config)

    def _load_config(self, config):
        tcfg = config.get("telegram") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(tcfg, dict):
            return
        self.token = tcfg.get("bot_token", "")
        self.allowed_users = tcfg.get("allowed_user_ids", [])
        self.enabled = bool(self.token)

    def start(self):
        """Start the background polling thread."""
        if not self.enabled or not self.token or not HAS_REQUESTS:
            if not HAS_REQUESTS:
                logger.warning("Telegram bridge: 'requests' not installed.")
            return False

        if self._running:
            return True

        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        logger.info("Telegram bridge started. Listening for messages...")
        return True

    def stop(self):
        """Stop the polling thread."""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5)
            self._poll_thread = None
        logger.info("Telegram bridge stopped.")

    def check(self):
        """
        Return new messages as list of (message, category) tuples.
        Called by the brain's module polling.
        """
        if not self.enabled:
            return []

        messages = []
        while self._messages:
            try:
                msg_data = self._messages.popleft()
                text = msg_data.get("text", "")
                sender = msg_data.get("sender", "Someone")
                if text:
                    messages.append((text, "love"))
                    logger.info(f"Telegram love note from {sender}: {text[:30]}...")
            except IndexError:
                break
        return messages

    def _poll_loop(self):
        """Background thread: long-poll Telegram for new messages."""
        url = self.API_BASE.format(token=self.token)

        while self._running:
            try:
                params = {
                    "offset": self._last_update_id + 1,
                    "timeout": 10,
                    "allowed_updates": ["message"]
                }
                resp = requests.get(
                    f"{url}/getUpdates",
                    params=params,
                    timeout=15
                )

                if resp.status_code != 200:
                    logger.warning(f"Telegram API error: {resp.status_code}")
                    time.sleep(self._poll_interval)
                    continue

                data = resp.json()
                if not data.get("ok"):
                    logger.warning(f"Telegram API returned not ok: {data}")
                    time.sleep(self._poll_interval)
                    continue

                for update in data.get("result", []):
                    update_id = update.get("update_id", 0)
                    if update_id > self._last_update_id:
                        self._last_update_id = update_id

                    message = update.get("message", {})
                    if not message:
                        continue

                    # Extract sender info
                    from_user = message.get("from", {})
                    user_id = from_user.get("id", 0)
                    first_name = from_user.get("first_name", "Someone")

                    # Filter by allowed users (if configured)
                    if self.allowed_users and user_id not in self.allowed_users:
                        logger.debug(f"Telegram: ignoring message from unauthorized user {user_id}")
                        continue

                    text = message.get("text", "")
                    if text:
                        self._messages.append({
                            "text": text,
                            "sender": first_name,
                            "user_id": user_id,
                            "timestamp": message.get("date", 0)
                        })

            except requests.exceptions.Timeout:
                continue  # Normal for long-polling
            except requests.exceptions.ConnectionError:
                logger.warning("Telegram: connection error, retrying...")
                time.sleep(5)
            except Exception as e:
                logger.warning(f"Telegram poll error: {e}")
                time.sleep(self._poll_interval)

    def send_reply(self, chat_id, text):
        """Send a reply back to the Telegram chat (optional fish responses)."""
        if not self.token or not HAS_REQUESTS:
            return False
        try:
            url = self.API_BASE.format(token=self.token)
            resp = requests.post(
                f"{url}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Telegram send error: {e}")
            return False

    def get_bot_info(self):
        """Get bot information (useful for setup verification)."""
        if not self.token or not HAS_REQUESTS:
            return None
        try:
            url = self.API_BASE.format(token=self.token)
            resp = requests.get(f"{url}/getMe", timeout=10)
            if resp.status_code == 200:
                return resp.json().get("result", {})
        except Exception as e:
            logger.warning(f"Telegram getMe error: {e}")
        return None
