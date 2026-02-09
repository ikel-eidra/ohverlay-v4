"""
Health & Wellness reminder module - LLM-enhanced.
Uses the LLM Brain for contextual, personalized reminders when available.
Falls back to curated static messages when LLM is unavailable.
"""

import time
from datetime import datetime
from utils.logger import logger


class HealthModule:
    """Generates health reminders, optionally enhanced by LLM for contextual awareness."""

    FALLBACK_REMINDERS = {
        "water": [
            "Time to drink some water!",
            "Stay hydrated - grab a glass of water.",
            "Water break! Your body will thank you.",
            "Hydration check! Have you had water recently?",
            "Your cells are thirsty. Water time!",
            "A sip of water keeps the focus sharp.",
        ],
        "eyes": [
            "20-20-20 Rule: Look 20ft away for 20 seconds.",
            "Give your eyes a rest - look away from the screen.",
            "Eye break time! Focus on something distant.",
            "Rest your eyes for a moment. You deserve it.",
            "Your eyes have been working hard. Let them rest.",
            "Blink, breathe, look away. Your eyes say thanks.",
        ],
        "posture": [
            "Posture check! Sit up straight.",
            "How's your posture? Shoulders back, spine aligned.",
            "Quick posture reset - straighten up!",
            "Roll your shoulders back and sit tall.",
            "Your spine called. It wants some love.",
            "Uncurl those shoulders. Stand tall even sitting.",
        ],
        "stretch": [
            "Time for a quick stretch!",
            "Stand up and stretch for a minute.",
            "Stretch break! Move your body.",
            "Take a moment to stretch your arms and neck.",
            "Your muscles need a moment. Stretch it out!",
            "Movement is medicine. Quick stretch?",
        ],
    }

    def __init__(self, config=None, llm_brain=None):
        self.enabled = True
        self.llm_brain = llm_brain
        self.intervals = {
            "water": 30 * 60,
            "eyes": 20 * 60,
            "posture": 45 * 60,
            "stretch": 60 * 60,
        }
        self.last_triggered = {k: time.time() for k in self.intervals}
        self._reminder_index = {k: 0 for k in self.intervals}
        self._pending_llm = {}  # key -> pending LLM result

        if config:
            self._load_config(config)

    def set_llm_brain(self, llm_brain):
        """Attach LLM brain for intelligent reminders."""
        self.llm_brain = llm_brain

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
        hour = datetime.now().hour
        messages = []

        for key, interval in self.intervals.items():
            if now - self.last_triggered[key] >= interval:
                self.last_triggered[key] = now

                # Try LLM-generated reminder first
                msg = None
                if self.llm_brain and self.llm_brain.is_available:
                    try:
                        msg = self.llm_brain.generate_health_reminder(key, hour)
                    except Exception as e:
                        logger.debug(f"LLM health reminder failed: {e}")

                # Fallback to static
                if not msg:
                    reminders = self.FALLBACK_REMINDERS[key]
                    idx = self._reminder_index[key] % len(reminders)
                    msg = reminders[idx]
                    self._reminder_index[key] = idx + 1

                messages.append((msg, "health"))
                logger.debug(f"Health reminder ({key}): {msg[:40]}...")

        return messages
