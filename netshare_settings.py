"""
Minimal settings manager for NetShare standalone app.
Stores only what's needed: network_sharing config.
"""

import json
import os
from copy import deepcopy

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".netshare")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "network_sharing": {
        "enabled": False,
        "my_folder": "",
        "my_username": "",
        "peers": [],
        "check_interval_seconds": 30,
        "log_path": "",
    },
    "bubbles": {
        "max_visible": 5,
        "display_duration_seconds": 10,
    },
    "app": {
        "version": "1.0.0",
    },
}


class NetShareSettings:
    def __init__(self):
        self._config = {}
        self.load()

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    saved = json.load(f)
                self._config = self._deep_merge(DEFAULT_CONFIG, saved)
            except (json.JSONDecodeError, IOError):
                self._config = deepcopy(DEFAULT_CONFIG)
        else:
            self._config = deepcopy(DEFAULT_CONFIG)
            self.save()

    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self._config, f, indent=2)
        except IOError:
            pass

    def get(self, section, key=None):
        if key is None:
            return self._config.get(section, {})
        return self._config.get(section, {}).get(key)

    def set(self, section, key, value):
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self.save()

    @staticmethod
    def _deep_merge(base, override):
        result = deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = NetShareSettings._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
