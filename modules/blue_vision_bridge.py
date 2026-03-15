"""
Blue Vision Bridge - Ohverlay v4.0
Connects Blue's vision system to the creature behavioral AI.

The creatures (jellyfish, fish, etc.) react to what's on the user's screen:
- Stressed screen (many tabs, long code sessions) → creatures slow down, glow calmer
- Idle screen (screensaver, desktop) → creatures become playful, dart around
- Work patterns detected → creatures remind user of breaks (20-20-20 rule)
- Creative content (art, design) → creatures get excited, vibrant colors
"""

import time
import threading
from utils.logger import logger

try:
    from modules.blue_vision import BlueVision
    HAS_VISION = True
except ImportError:
    HAS_VISION = False


class ScreenContext:
    """Holds the current screen analysis context for creature behavior."""

    def __init__(self):
        self.stress_level = 0.0       # 0-1: how stressed the screen looks
        self.activity_type = "unknown" # work, creative, idle, gaming, browsing, coding
        self.work_duration = 0.0       # estimated minutes of continuous work
        self.needs_break = False       # should suggest a break?
        self.screen_summary = ""       # last analysis text
        self.last_update = 0           # timestamp of last analysis
        self.mood_modifier = 0.0       # -20 to +20 mood adjustment
        self.speed_modifier = 1.0      # 0.5 to 1.5 speed multiplier
        self.dart_chance_modifier = 0.0 # extra dart probability
        self.should_flare = False      # trigger a display flare?
        self.bubble_message = ""       # message for bubble system


class BlueVisionBridge:
    """
    Bridges Blue Vision → Creature Brain.
    Periodically captures screen, analyzes context, and feeds behavioral
    modifiers into the creature's BehavioralReactor.
    """

    # Analysis prompt tuned for behavioral output
    SCREEN_ANALYSIS_PROMPT = (
        "Analyze this screen briefly. Classify the activity as ONE of: "
        "work, coding, creative, gaming, browsing, idle, video, reading. "
        "Rate stress level 0-10 (0=relaxed, 10=very busy/stressed). "
        "Estimate how long the user might have been working (minutes). "
        "Should the user take a break? "
        "Reply in this exact format:\n"
        "ACTIVITY: <type>\n"
        "STRESS: <0-10>\n"
        "WORK_MINS: <number>\n"
        "BREAK: <yes/no>\n"
        "SUMMARY: <one sentence>"
    )

    def __init__(self, api_key=None, scan_interval=300):
        """
        Args:
            api_key: Groq API key for vision
            scan_interval: Seconds between screen scans (default 5 min)
        """
        self.context = ScreenContext()
        self.scan_interval = max(60, scan_interval)  # minimum 1 minute
        self._running = False
        self._thread = None
        self._vision = None
        self._consecutive_work_scans = 0
        self._last_break_reminder = 0

        if HAS_VISION:
            self._vision = BlueVision(api_key=api_key)
            # Override cooldown for bridge (we manage our own timing)
            self._vision.cooldown = 0
        else:
            logger.warning("BlueVisionBridge: blue_vision module not available")

    @property
    def available(self):
        return self._vision is not None and bool(self._vision.api_key)

    def set_api_key(self, key):
        if self._vision:
            self._vision.set_api_key(key)

    def start(self):
        """Start background screen scanning."""
        if not self.available:
            logger.info("BlueVisionBridge: not starting (no vision or API key)")
            return

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        logger.info(f"BlueVisionBridge started (scan every {self.scan_interval}s)")

    def stop(self):
        self._running = False

    def _scan_loop(self):
        """Background loop: capture → analyze → update context."""
        # Initial delay to let app settle
        time.sleep(10)

        while self._running:
            try:
                self._do_scan()
            except Exception as e:
                logger.warning(f"VisionBridge scan error: {e}")

            time.sleep(self.scan_interval)

    def _do_scan(self):
        """Single scan cycle."""
        if not self._vision:
            return

        b64, w, h = self._vision.capture_screenshot(max_size=512)
        if not b64:
            return

        result = self._vision.analyze_image(
            b64,
            prompt=self.SCREEN_ANALYSIS_PROMPT,
            context="Analyzing for creature behavioral AI"
        )

        if not result or result.startswith("Error"):
            logger.debug(f"VisionBridge: analysis failed: {result}")
            return

        self._parse_and_update(result)

    def _parse_and_update(self, analysis_text):
        """Parse vision analysis into behavioral modifiers."""
        ctx = self.context
        ctx.screen_summary = analysis_text
        ctx.last_update = time.time()

        # Parse structured response
        activity = "unknown"
        stress = 5
        work_mins = 0
        needs_break = False

        for line in analysis_text.split("\n"):
            line = line.strip().upper()
            if line.startswith("ACTIVITY:"):
                activity = line.split(":", 1)[1].strip().lower()
            elif line.startswith("STRESS:"):
                try:
                    stress = int(line.split(":", 1)[1].strip().split()[0])
                    stress = max(0, min(10, stress))
                except (ValueError, IndexError):
                    pass
            elif line.startswith("WORK_MINS:"):
                try:
                    work_mins = int(line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("BREAK:"):
                needs_break = "yes" in line.lower()
            elif line.startswith("SUMMARY:"):
                ctx.screen_summary = line.split(":", 1)[1].strip()

        ctx.activity_type = activity
        ctx.stress_level = stress / 10.0
        ctx.work_duration = work_mins
        ctx.needs_break = needs_break

        # Track consecutive work scans for break reminders
        if activity in ("work", "coding", "reading") and stress >= 4:
            self._consecutive_work_scans += 1
        else:
            self._consecutive_work_scans = max(0, self._consecutive_work_scans - 1)

        # --- Compute behavioral modifiers ---

        # Mood modifier: stressed screen → lower mood, idle → higher mood
        if stress >= 7:
            ctx.mood_modifier = -10.0
        elif stress >= 5:
            ctx.mood_modifier = -3.0
        elif stress <= 2:
            ctx.mood_modifier = 8.0
        else:
            ctx.mood_modifier = 0.0

        # Speed modifier: stressed → creatures move slower (calming), idle → faster (playful)
        if activity == "idle":
            ctx.speed_modifier = 1.3
            ctx.dart_chance_modifier = 0.08  # more darting when idle
        elif activity in ("gaming", "video"):
            ctx.speed_modifier = 1.1
            ctx.dart_chance_modifier = 0.04
        elif stress >= 6:
            ctx.speed_modifier = 0.7  # calmer movement when user is stressed
            ctx.dart_chance_modifier = -0.02
        elif activity == "creative":
            ctx.speed_modifier = 1.15
            ctx.dart_chance_modifier = 0.05
            ctx.mood_modifier = 5.0  # creatures get inspired too
        else:
            ctx.speed_modifier = 1.0
            ctx.dart_chance_modifier = 0.0

        # Flare trigger: occasional display when user seems stressed
        ctx.should_flare = stress >= 7 and self._consecutive_work_scans >= 2

        # Break reminder via bubble
        now = time.time()
        ctx.bubble_message = ""
        if needs_break and (now - self._last_break_reminder > 1200):  # max every 20 min
            self._last_break_reminder = now
            if work_mins >= 40:
                ctx.bubble_message = "You've been working hard! Try the 20-20-20 rule: look 20ft away for 20 seconds."
            elif stress >= 7:
                ctx.bubble_message = "Your screen looks busy. Take a deep breath and stretch!"
            else:
                ctx.bubble_message = "Time for a quick break? Your eyes will thank you."

        logger.info(
            f"VisionBridge: activity={activity} stress={stress}/10 "
            f"work={work_mins}min break={needs_break} mood_mod={ctx.mood_modifier:+.0f}"
        )

    def apply_to_brain(self, brain, bubble_system=None):
        """
        Apply current screen context to a BehavioralReactor.
        Call this periodically from the main loop (e.g. every few seconds).
        """
        ctx = self.context

        # Don't apply stale context (older than 2x scan interval)
        if time.time() - ctx.last_update > self.scan_interval * 2.5:
            return

        # Mood influence (gentle, not overwhelming)
        if ctx.mood_modifier != 0:
            brain.mood = max(0.0, min(100.0, brain.mood + ctx.mood_modifier * 0.01))

        # Flare trigger
        if ctx.should_flare and brain.state == "IDLE":
            brain.state = "FLARING"
            brain._flare_timer = 0.0
            ctx.should_flare = False  # one-shot

        # Bubble messages
        if ctx.bubble_message and bubble_system:
            bubble_system.queue_message(ctx.bubble_message, "health")
            ctx.bubble_message = ""  # consume

    def get_context_for_chat(self):
        """Return screen context string for Blue chatbot's system prompt."""
        ctx = self.context
        if time.time() - ctx.last_update > self.scan_interval * 3:
            return ""

        parts = []
        if ctx.activity_type != "unknown":
            parts.append(f"User activity: {ctx.activity_type}")
        if ctx.stress_level > 0:
            parts.append(f"Stress level: {ctx.stress_level:.0%}")
        if ctx.work_duration > 0:
            parts.append(f"Working for ~{ctx.work_duration} minutes")
        if ctx.needs_break:
            parts.append("User should take a break")
        if ctx.screen_summary:
            parts.append(f"Screen: {ctx.screen_summary}")

        return " | ".join(parts) if parts else ""
