"""
Love Notes module ("Connection Mode").
Reads messages from a local JSON file or shared folder.
A loved one can save messages that the fish delivers via bubbles.
"""

import json
import os
import time
from utils.logger import logger


class LoveNotesModule:
    """Reads love notes from a JSON file and delivers them via the fish."""

    def __init__(self, config=None):
        self.enabled = True
        self.source_path = ""
        self.check_interval = 5 * 60  # seconds
        self.last_check = 0
        self.last_modified = 0
        self.delivered_notes = set()
        self.pending_notes = []

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
        logger.info(f"Love notes source set to: {path}")

    def check(self):
        """Check for new love notes. Returns list of (message, category) tuples."""
        if not self.enabled or not self.source_path:
            return []

        now = time.time()
        if now - self.last_check < self.check_interval:
            return []
        self.last_check = now

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

            # Support both single note and array formats
            # {"message": "I love you"} or {"notes": [{"message": "..."}, ...]}
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
                    logger.info(f"New love note found: {msg[:30]}...")

        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"Error reading love notes: {e}")

        return messages
