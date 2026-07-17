"""
Configuration management with JSON persistence.
All user settings are stored locally and loaded on startup.
"""

import json
import os
import shutil
from utils.logger import logger

APP_DIR_NAME = ".ohverlay"

DEFAULT_CONFIG = {
    "overlays": {
        "fireflies": True,
        "dragonflies": False,
        "dandelions": False
    },
    "hotkeys": {
        "toggle_visibility": "ctrl+alt+h",
        "toggle_interactivity": "ctrl+alt+i"
    },
    "app": {
        "version": "1.0.0"
    }
}


def get_app_data_dir():
    """Return the writable application data directory."""
    override = os.environ.get("OHVERLAY_HOME", "").strip()
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(os.path.expanduser("~"), APP_DIR_NAME)


def get_config_path(config_dir=None):
    """Return the JSON settings file path for the active app data directory."""
    target_dir = os.path.abspath(config_dir or get_app_data_dir())
    return os.path.join(target_dir, "config.json")


CONFIG_DIR = get_app_data_dir()
CONFIG_PATH = get_config_path(CONFIG_DIR)


class Settings:
    """Manages reading and writing application preferences with JSON persistence."""

    def __init__(self, config_path=None):
        self.config_path = os.path.abspath(config_path or CONFIG_PATH)
        self.config_dir = os.path.dirname(self.config_path)
        self.data = DEFAULT_CONFIG.copy()

        # Ensure directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        self.load()

    def load(self):
        """Load settings from the JSON file, or create it if missing."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    self._merge(self.data, user_data)
                logger.debug(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config {self.config_path}, using defaults: {e}")
                self.save()  # Overwrite corrupted file
        else:
            logger.info("No config file found. Creating default config.")
            self.save()

    def save(self):
        """Write the current settings back to disk atomically."""
        try:
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            shutil.move(temp_path, self.config_path)
            logger.debug("Settings saved.")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def _merge(self, default_dict, user_dict):
        """Recursively merge user settings into the default structure."""
        for key, value in default_dict.items():
            if key in user_dict:
                if isinstance(value, dict) and isinstance(user_dict[key], dict):
                    self._merge(value, user_dict[key])
                else:
                    default_dict[key] = user_dict[key]

    def get(self, section, key=None):
        """Retrieve a section or a specific key within a section."""
        if key is None:
            return self.data.get(section, {})
        return self.data.get(section, {}).get(key)

    def set(self, section, key, value):
        """Update a specific key within a section and save to disk."""
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
        self.save()
