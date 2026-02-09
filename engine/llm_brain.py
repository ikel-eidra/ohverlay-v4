"""
LLM Brain - The intelligent orchestrator for ZenFish.
Uses Claude (Anthropic) or OpenAI to generate contextual, personalized
health reminders, curate news into bite-sized summaries, and add personality
to the fish's communication.
"""

import threading
import time
import json
from collections import deque
from utils.logger import logger

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class LLMBrain:
    """
    Orchestrates health reminders, news curation, and message personality
    through a capable LLM (Claude preferred, OpenAI fallback).
    """

    SYSTEM_PROMPT = """You are the mind of a beautiful Betta fish named ZenFish, a desktop companion
that cares deeply about your human's wellbeing. You communicate through small bubbles that float
across their screen.

Your personality:
- Warm, caring, gentle but not saccharine
- Aware of time of day and work patterns
- Brief and impactful (messages must be under 80 characters for bubble display)
- You mix practical advice with emotional warmth
- Occasionally poetic or playful

CRITICAL: Every response must be a single short message (under 80 chars). No quotes, no prefixes,
no explanations. Just the message itself."""

    def __init__(self, config=None):
        self.provider = "none"
        self.anthropic_key = ""
        self.openai_key = ""
        self.model = ""
        self._client = None
        self._lock = threading.Lock()
        self._cache = deque(maxlen=50)
        self._last_request = 0
        self._min_interval = 5.0  # Min seconds between API calls

        if config:
            self._load_config(config)
        self._init_client()

    def _load_config(self, config):
        lcfg = config.get("llm") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(lcfg, dict):
            return
        self.provider = lcfg.get("provider", "anthropic")
        self.anthropic_key = lcfg.get("anthropic_api_key", "")
        self.openai_key = lcfg.get("openai_api_key", "")
        self.model = lcfg.get("model", "")

    def _init_client(self):
        """Initialize the LLM client based on available provider and keys."""
        if self.provider == "anthropic" and self.anthropic_key and HAS_ANTHROPIC:
            try:
                self._client = anthropic.Anthropic(api_key=self.anthropic_key)
                if not self.model:
                    self.model = "claude-sonnet-4-5-20250929"
                logger.info(f"LLM Brain initialized with Anthropic ({self.model})")
                return
            except Exception as e:
                logger.warning(f"Anthropic init failed: {e}")

        if self.provider == "openai" and self.openai_key and HAS_OPENAI:
            try:
                self._client = openai.OpenAI(api_key=self.openai_key)
                if not self.model:
                    self.model = "gpt-4o-mini"
                logger.info(f"LLM Brain initialized with OpenAI ({self.model})")
                return
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")

        # Auto-detect: try anthropic first, then openai
        if not self._client and self.anthropic_key and HAS_ANTHROPIC:
            try:
                self._client = anthropic.Anthropic(api_key=self.anthropic_key)
                self.provider = "anthropic"
                if not self.model:
                    self.model = "claude-sonnet-4-5-20250929"
                logger.info(f"LLM Brain auto-detected Anthropic ({self.model})")
                return
            except Exception:
                pass

        if not self._client and self.openai_key and HAS_OPENAI:
            try:
                self._client = openai.OpenAI(api_key=self.openai_key)
                self.provider = "openai"
                if not self.model:
                    self.model = "gpt-4o-mini"
                logger.info(f"LLM Brain auto-detected OpenAI ({self.model})")
                return
            except Exception:
                pass

        if not self._client:
            logger.warning("LLM Brain: No API key configured. Using fallback static messages.")
            self.provider = "none"

    @property
    def is_available(self):
        return self._client is not None

    def generate(self, prompt, context=""):
        """
        Generate a short message from the LLM. Thread-safe, rate-limited.
        Returns the message string, or None if unavailable/failed.
        """
        if not self._client:
            return None

        # Rate limiting
        now = time.time()
        if now - self._last_request < self._min_interval:
            return None

        def _call():
            try:
                with self._lock:
                    self._last_request = time.time()

                    full_prompt = prompt
                    if context:
                        full_prompt = f"Context: {context}\n\n{prompt}"

                    if self.provider == "anthropic":
                        response = self._client.messages.create(
                            model=self.model,
                            max_tokens=100,
                            system=self.SYSTEM_PROMPT,
                            messages=[{"role": "user", "content": full_prompt}]
                        )
                        msg = response.content[0].text.strip()
                    elif self.provider == "openai":
                        response = self._client.chat.completions.create(
                            model=self.model,
                            max_tokens=100,
                            messages=[
                                {"role": "system", "content": self.SYSTEM_PROMPT},
                                {"role": "user", "content": full_prompt}
                            ]
                        )
                        msg = response.choices[0].message.content.strip()
                    else:
                        return None

                    # Truncate if somehow over 80 chars
                    if len(msg) > 80:
                        msg = msg[:77] + "..."

                    self._cache.append(msg)
                    return msg

            except Exception as e:
                logger.warning(f"LLM generation failed: {e}")
                return None

        return _call()

    def generate_async(self, prompt, context="", callback=None):
        """Non-blocking generation. Calls callback(message) when done."""
        def _worker():
            result = self.generate(prompt, context)
            if callback and result:
                callback(result)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def generate_health_reminder(self, reminder_type, hour_of_day):
        """Generate a contextual health reminder using LLM."""
        time_context = "morning" if hour_of_day < 12 else "afternoon" if hour_of_day < 17 else "evening"
        prompts = {
            "water": f"It's {time_context}. Generate a caring hydration reminder. Be creative, not generic.",
            "eyes": f"It's {time_context}. Generate an eye-care reminder (20-20-20 rule). Make it feel personal.",
            "posture": f"It's {time_context}. Generate a posture check reminder. Be encouraging.",
            "stretch": f"It's {time_context}. Generate a stretch/movement reminder. Be motivating.",
        }
        prompt = prompts.get(reminder_type, f"Generate a {reminder_type} wellness reminder for {time_context}.")
        return self.generate(prompt)

    def summarize_headline(self, headline):
        """Summarize a news headline into a fish-friendly bubble message."""
        prompt = (
            f"Rewrite this news headline as a brief, digestible update for someone focused on work. "
            f"Keep it informative but calming. Under 80 characters.\n\n"
            f"Headline: {headline}"
        )
        return self.generate(prompt)

    def curate_news(self, headlines):
        """
        Given a list of headlines, pick the most relevant one and summarize it.
        Returns (summary, original_headline) or None.
        """
        if not headlines:
            return None

        prompt = (
            f"From these headlines, pick the single most important one that a busy professional "
            f"should know about. Rewrite it as a short, calm informational bubble (under 80 chars).\n\n"
            f"Headlines:\n" + "\n".join(f"- {h}" for h in headlines[:10])
        )
        result = self.generate(prompt)
        return result

    def personalize_love_note(self, raw_message, sender_name=""):
        """Optionally add fish personality to a love note delivery."""
        # Love notes are personal - we pass them through mostly as-is
        # but the fish can add a tiny warm intro
        if len(raw_message) <= 60:
            return raw_message
        # Truncate long messages for bubble display
        return raw_message[:77] + "..."
