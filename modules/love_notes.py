"""
Love Notes module ("Connection Mode") - Multi-source.

Sources (all feed into the same bubble stream):
1. Local JSON file - partner saves a note.json
2. Telegram Bot - partner messages the bot in real-time
3. Webhook - WhatsApp/Messenger via automation (IFTTT, Zapier, n8n)

The fish delivers all messages as love-category bubbles.
"""

import json
import os
import time
from utils.logger import logger


class LoveNotesModule:
    """
    Aggregates love notes from multiple sources:
    - Local JSON file
    - Telegram bridge (set externally)
    - Webhook server (set externally)
    """

    def __init__(self, config=None):
        self.enabled = True
        self.source_path = ""
        self.check_interval = 5 * 60  # seconds for file check
        self.last_file_check = 0
        self.last_modified = 0
        self.delivered_notes = set()

        # External sources (set by main.py after init)
        self.telegram_bridge = None
        self.webhook_server = None

        if config:
            self._load_config(config)

    def _load_config(self, config):
        lcfg = config.get("love_notes") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(lcfg, dict):
            return
        self.source_path = lcfg.get("source_path", self.source_path)
        self.check_interval = lcfg.get("check_interval_minutes", 5) * 60

    def set_source_path(self, path):
        """Set the path to the love notes JSON file."""
        self.source_path = path
        self.delivered_notes.clear()
        self.last_modified = 0
        logger.info(f"Love notes file source set to: {path}")

    def set_telegram_bridge(self, bridge):
        """Attach Telegram bridge for real-time notes."""
        self.telegram_bridge = bridge

    def set_webhook_server(self, server):
        """Attach webhook server for WhatsApp/Messenger notes."""
        self.webhook_server = server

    def check(self):
        """
        Check ALL sources for new love notes.
        Returns list of (message, category) tuples.
        """
        if not self.enabled:
            return []

        messages = []

        # Source 1: Local JSON file
        messages.extend(self._check_file())

        # Source 2: Telegram (real-time)
        if self.telegram_bridge:
            try:
                telegram_msgs = self.telegram_bridge.check()
                messages.extend(telegram_msgs)
            except Exception as e:
                logger.warning(f"Telegram check error: {e}")

        # Source 3: Webhook (WhatsApp/Messenger)
        if self.webhook_server:
            try:
                webhook_msgs = self.webhook_server.check()
                messages.extend(webhook_msgs)
            except Exception as e:
                logger.warning(f"Webhook check error: {e}")

        return messages

    def _check_file(self):
        """Check the local JSON file for new notes."""
        if not self.source_path:
            return []

        now = time.time()
        if now - self.last_file_check < self.check_interval:
            return []
        self.last_file_check = now

        messages = []
        try:
            if not os.path.exists(self.source_path):
                return []

            mtime = os.path.getmtime(self.source_path)
            if mtime <= self.last_modified:
                return []
            self.last_modified = mtime

            with open(self.source_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Support multiple formats:
            # {"message": "I love you"}
            # {"notes": [{"message": "..."}, ...]}
            # [{"message": "..."}, ...]
            # ["plain string", ...]
            notes = []
            if isinstance(data, dict):
                if "notes" in data:
                    notes = data["notes"]
                elif "message" in data:
                    notes = [data]
            elif isinstance(data, list):
                notes = data

            for note in notes:
                msg = note.get("message", "") if isinstance(note, dict) else str(note)
                if msg and msg not in self.delivered_notes:
                    messages.append((msg, "love"))
                    self.delivered_notes.add(msg)
                    logger.info(f"New love note from file: {msg[:30]}...")

        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"Error reading love notes file: {e}")

        return messages
