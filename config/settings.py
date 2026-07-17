"""
Configuration management with JSON persistence.
All user settings are stored locally and loaded on startup.
"""

import json
import os
from utils.logger import logger

APP_DIR_NAME = ".ohverlay"
LEGACY_APP_DIR_NAME = ".zenfish"

DEFAULT_CONFIG = {
    "creature_type": "overlay-platform",
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
        "motion_profile": "realistic_v2",
        "school_size": 5,
        "size": "medium"
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
    "overlays": {
        "glass-fish": False,
        "betta-fish": False,
        "paper-lanterns": True
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
    "ambient": {
        "falling_leaves_enabled": True,
        "falling_leaves_interval_seconds": 300,
        "falling_leaves_burst_min": 6,
        "falling_leaves_burst_max": 8
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
        "toggle_visibility": "ctrl+alt+h",
        "toggle_interactivity": "ctrl+alt+i"
    },
    "app": {
        "version": "4.0.0",
        "support_email": "support@ohverlay.com",
        "download_url": "https://ohverlay.com/download",
        "public_website_enabled": True,
        "website_release_stage": "beta",
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


def get_app_data_dir():
    """Return the writable application data directory."""
    override = os.environ.get("OHVERLAY_HOME", "").strip()
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(os.path.expanduser("~"), APP_DIR_NAME)


def get_legacy_app_data_dir():
    """Return the legacy ZenFish data directory used by older builds."""
    return os.path.join(os.path.expanduser("~"), LEGACY_APP_DIR_NAME)


def get_config_path(config_dir=None):
    """Return the JSON settings file path for the active app data directory."""
    target_dir = os.path.abspath(config_dir or get_app_data_dir())
    return os.path.join(target_dir, "config.json")


def get_legacy_config_path():
    """Return the old ZenFish config path for one-time migration."""
    return os.path.join(get_legacy_app_data_dir(), "config.json")


def get_updates_dir(config_dir=None):
    """Return the update download directory for the active app data directory."""
    target_dir = os.path.abspath(config_dir or get_app_data_dir())
    return os.path.join(target_dir, "updates")


CONFIG_DIR = get_app_data_dir()
CONFIG_PATH = get_config_path(CONFIG_DIR)


class Settings:
    """Manages application configuration with JSON file persistence."""

    def __init__(self):
        self._config = {}
        self.config_dir = get_app_data_dir()
        self.config_path = get_config_path(self.config_dir)
        self.legacy_config_path = get_legacy_config_path()
        self.load()

    def load(self):
        """Load config from disk, merging with defaults for any missing keys."""
        source_path = self.config_path
        migrating_legacy = False

        if not os.path.exists(source_path) and os.path.exists(self.legacy_config_path):
            source_path = self.legacy_config_path
            migrating_legacy = True

        if os.path.exists(source_path):
            try:
                with open(source_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._config = self._deep_merge(DEFAULT_CONFIG, saved)
                if migrating_legacy:
                    self.save()
                    logger.info(
                        f"Configuration migrated from {source_path} to {self.config_path}"
                    )
                else:
                    logger.info(f"Configuration loaded from {source_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Config load failed ({e}), using defaults.")
                self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        else:
            self._config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()
            logger.info(f"Default configuration created at {self.config_path}")

    def save(self):
        """Persist current config to disk."""
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
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
