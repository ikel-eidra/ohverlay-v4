import json

import config.settings as settings_module
from config.settings import (
    DEFAULT_CONFIG,
    Settings,
    get_app_data_dir,
)

def test_default_config_structure():
    assert "overlays" in DEFAULT_CONFIG
    assert "hotkeys" in DEFAULT_CONFIG
    assert "app" in DEFAULT_CONFIG

def test_settings_merge():
    settings = Settings(config_path="dummy.json")
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    override = {"a": {"b": 10}, "e": 5}
    settings._merge(base, override)
    assert base["a"]["b"] == 10
    assert base["a"]["c"] == 2
    assert base["d"] == 3
    # "e" is not in base, so it is ignored by design
    assert "e" not in base

def test_settings_get_set(tmp_path):
    config_file = tmp_path / ".ohverlay" / "config.json"
    settings = Settings(config_path=str(config_file))
    settings.set("overlays", "fireflies", True)
    assert settings.get("overlays", "fireflies") is True
    assert config_file.exists()

def test_app_data_helpers_respect_env_override(tmp_path, monkeypatch):
    app_home = tmp_path / "custom-ohverlay-home"
    monkeypatch.setenv("OHVERLAY_HOME", str(app_home))
    assert get_app_data_dir() == str(app_home)
