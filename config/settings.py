"""
Configuration management with JSON persistence.
All user settings are stored locally and loaded on startup.
"""

import json
import os
from utils.logger import logger

DEFAULT_CONFIG = {
    "fish": {
        "primary_color": [255, 118, 54],
        "secondary_color": [35, 84, 170],
        "accent_color": [255, 240, 235],
        "betta_palette": "nemo_galaxy",
        "opacity": 0.9,
        "size_scale": 1.0,
        "color_mode": "gradient",
        "color_shift_speed": 0.3,
        "enable_glow": True,
        "silhouette_strength": 1.0,
        "eye_tracking_strength": 0.75,
        "eye_tracking_damping": 0.18,
        "motion_profile": "realistic_v2"
    },
    "sanctuary": {
        "enabled": False,
        "zones": [],
        "monitor_exclusions": [],
        "repulsion_strength": 200.0,
        "repulsion_margin": 80
    },
    "modules": {
        "health": True,
        "news": False,
        "love_notes": True,
        "schedule": True
    },
    "health": {
        "water_reminder_minutes": 30,
        "eye_break_minutes": 20,
        "posture_check_minutes": 45,
        "stretch_reminder_minutes": 60
    },
    "love_notes": {
        "source_path": "",
        "check_interval_minutes": 5
    },
    "schedule": {
        "events": []
    },
    "news": {
        "rss_feeds": [],
        "check_interval_minutes": 30
    },
    "bubbles": {
        "enabled": True,
        "max_visible": 5,
        "display_duration_seconds": 8,
        "min_interval_seconds": 60
    },
    "hotkeys": {
        "feed_fish": "ctrl+alt+f",
        "toggle_sanctuary": "ctrl+alt+s",
        "toggle_visibility": "ctrl+alt+h"
    },
    "app": {
        "version": "1.0.0",
        "support_email": "support@ohverlay.com",
        "public_website_enabled": False,
        "website_release_stage": "private_prelaunch",
        "auto_update_enabled": True,
        "update_check_hours": 6,
        "update_manifest_url": "https://ohverlay.com/updates/manifest.json",
        "update_channel": "stable"
    },
    "llm": {
        "provider": "anthropic",
        "anthropic_api_key": "",
        "openai_api_key": "",
        "model": "",
        "enable_vision_foraging": False,
        "vision_interval_minutes": 60,
        "vision_model": "gpt-4o-mini"
    },
    "telegram": {
        "bot_token": "",
        "allowed_user_ids": []
    },
    "webhook": {
        "enabled": False,
        "port": 7277
    }
}

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".zenfish")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


class Settings:
    """Manages application configuration with JSON file persistence."""

    def __init__(self):
        self._config = {}
        self.load()

    def load(self):
        """Load config from disk, merging with defaults for any missing keys."""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    saved = json.load(f)
                self._config = self._deep_merge(DEFAULT_CONFIG, saved)
                logger.info(f"Configuration loaded from {CONFIG_PATH}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Config load failed ({e}), using defaults.")
                self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        else:
            self._config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()
            logger.info(f"Default configuration created at {CONFIG_PATH}")

    def save(self):
        """Persist current config to disk."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, section, key=None):
        """Get a config value. If key is None, returns the entire section."""
        if key is None:
            return self._config.get(section, {})
        return self._config.get(section, {}).get(key)

    def set(self, section, key, value):
        """Set a config value and persist to disk."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self.save()

    @staticmethod
    def _deep_merge(base, override):
        """Recursively merge override into base, keeping base keys as defaults."""
        result = json.loads(json.dumps(base))
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Settings._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
