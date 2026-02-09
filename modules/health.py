"""
Health & Wellness reminder module.
Generates periodic reminders for hydration, eye breaks, posture, and stretching.
"""

import time
from utils.logger import logger


class HealthModule:
    """Generates health reminders based on configurable intervals."""

    REMINDERS = {
        "water": [
            "Time to drink some water!",
            "Stay hydrated - grab a glass of water.",
            "Water break! Your body will thank you.",
            "Hydration check! Have you had water recently?",
        ],
        "eyes": [
            "20-20-20 Rule: Look at something 20ft away for 20 seconds.",
            "Give your eyes a rest - look away from the screen.",
            "Eye break time! Focus on something distant.",
            "Rest your eyes for a moment. You deserve it.",
        ],
        "posture": [
            "Posture check! Sit up straight.",
            "How's your posture? Shoulders back, spine aligned.",
            "Quick posture reset - straighten up!",
            "Roll your shoulders back and sit tall.",
        ],
        "stretch": [
            "Time for a quick stretch!",
            "Stand up and stretch for a minute.",
            "Stretch break! Move your body.",
            "Take a moment to stretch your arms and neck.",
        ],
    }

    def __init__(self, config=None):
        self.enabled = True
        self.intervals = {
            "water": 30 * 60,
            "eyes": 20 * 60,
            "posture": 45 * 60,
            "stretch": 60 * 60,
        }
        self.last_triggered = {k: time.time() for k in self.intervals}
        self._reminder_index = {k: 0 for k in self.intervals}

        if config:
            self._load_config(config)

    def _load_config(self, config):
        hcfg = config.get("health") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(hcfg, dict):
            return
        mapping = {
            "water_reminder_minutes": "water",
            "eye_break_minutes": "eyes",
            "posture_check_minutes": "posture",
            "stretch_reminder_minutes": "stretch",
        }
        for config_key, reminder_key in mapping.items():
            if config_key in hcfg:
                self.intervals[reminder_key] = hcfg[config_key] * 60

    def check(self):
        """Check all reminder timers. Returns list of (message, category) tuples."""
        if not self.enabled:
            return []

        now = time.time()
        messages = []

        for key, interval in self.intervals.items():
            if now - self.last_triggered[key] >= interval:
                reminders = self.REMINDERS[key]
                idx = self._reminder_index[key] % len(reminders)
                messages.append((reminders[idx], "health"))
                self._reminder_index[key] = idx + 1
                self.last_triggered[key] = now
                logger.debug(f"Health reminder triggered: {key}")

        return messages
