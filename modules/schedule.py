"""
Schedule module for time-based reminders.
Supports lunch reminders, meeting alerts, and custom timed events.
"""

import time
from datetime import datetime
from utils.logger import logger


class ScheduleModule:
    """Manages scheduled reminders and delivers them at the right time."""

    DEFAULT_EVENTS = [
        {"time": "12:00", "message": "Lunch time! Take a break and eat well.", "recurring": True},
        {"time": "15:00", "message": "Afternoon snack break!", "recurring": True},
    ]

    def __init__(self, config=None):
        self.enabled = True
        self.events = []
        self.triggered_today = set()
        self.last_date = ""

        if config:
            self._load_config(config)

        if not self.events:
            self.events = list(self.DEFAULT_EVENTS)

    def _load_config(self, config):
        scfg = config.get("schedule") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(scfg, dict):
            return
        events = scfg.get("events", [])
        if events:
            self.events = events

    def add_event(self, time_str, message, recurring=True):
        """Add a scheduled event. time_str format: 'HH:MM'."""
        self.events.append({
            "time": time_str,
            "message": message,
            "recurring": recurring
        })
        logger.info(f"Schedule event added: {time_str} - {message}")

    def remove_event(self, index):
        """Remove a scheduled event by index."""
        if 0 <= index < len(self.events):
            removed = self.events.pop(index)
            logger.info(f"Schedule event removed: {removed['message']}")

    def check(self):
        """Check if any scheduled events should fire now. Returns list of (message, category)."""
        if not self.enabled:
            return []

        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")

        # Reset triggered set on new day
        if current_date != self.last_date:
            self.triggered_today.clear()
            self.last_date = current_date

        messages = []
        for i, event in enumerate(self.events):
            event_time = event.get("time", "")
            event_msg = event.get("message", "")
            event_key = f"{i}:{event_time}"

            if not event_time or event_key in self.triggered_today:
                continue

            # Check if current time matches (within 1-minute window)
            if current_time == event_time:
                messages.append((event_msg, "schedule"))
                self.triggered_today.add(event_key)
                logger.info(f"Schedule event triggered: {event_msg}")

                # Remove non-recurring events
                if not event.get("recurring", True):
                    self.events[i] = None

        # Clean up removed events
        self.events = [e for e in self.events if e is not None]

        return messages
