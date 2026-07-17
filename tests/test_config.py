import json

import config.settings as settings_module
from config.settings import (
    DEFAULT_CONFIG,
    Settings,
    get_app_data_dir,
    get_updates_dir,
)


def test_default_config_structure():
    assert "fish" in DEFAULT_CONFIG
    assert "sanctuary" in DEFAULT_CONFIG
    assert "modules" in DEFAULT_CONFIG
    assert "ambient" in DEFAULT_CONFIG
    assert "bubbles" in DEFAULT_CONFIG
    assert "hotkeys" in DEFAULT_CONFIG


def test_settings_deep_merge():
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    override = {"a": {"b": 10}, "e": 5}
    result = Settings._deep_merge(base, override)
    assert result["a"]["b"] == 10
    assert result["a"]["c"] == 2
    assert result["d"] == 3
    assert result["e"] == 5


def test_settings_get_set(tmp_path, monkeypatch):
    monkeypatch.setenv("OHVERLAY_HOME", str(tmp_path / ".ohverlay"))
    settings = Settings()
    settings.set("fish", "primary_color", [255, 0, 0])
    assert settings.get("fish", "primary_color") == [255, 0, 0]
    assert (tmp_path / ".ohverlay" / "config.json").exists()


def test_default_betta_palette_present():
    assert DEFAULT_CONFIG["fish"]["betta_palette"] == "nemo_galaxy"


def test_fish_visual_tuning_defaults_present():
    assert DEFAULT_CONFIG["fish"]["silhouette_strength"] == 1.0
    assert DEFAULT_CONFIG["fish"]["eye_tracking_strength"] == 0.75
    assert DEFAULT_CONFIG["fish"]["eye_tracking_damping"] == 0.18


def test_app_release_defaults_present():
    assert DEFAULT_CONFIG["app"]["public_website_enabled"] is True
    assert DEFAULT_CONFIG["app"]["website_release_stage"] == "beta"


def test_ambient_leaf_defaults_present():
    assert DEFAULT_CONFIG["ambient"]["falling_leaves_enabled"] is True
    assert DEFAULT_CONFIG["ambient"]["falling_leaves_interval_seconds"] == 300
    assert DEFAULT_CONFIG["ambient"]["falling_leaves_burst_min"] == 6
    assert DEFAULT_CONFIG["ambient"]["falling_leaves_burst_max"] == 8


def test_app_data_helpers_respect_env_override(tmp_path, monkeypatch):
    app_home = tmp_path / "custom-ohverlay-home"
    monkeypatch.setenv("OHVERLAY_HOME", str(app_home))
    assert get_app_data_dir() == str(app_home)
    assert get_updates_dir() == str(app_home / "updates")


def test_settings_migrate_from_legacy_zenfish_dir(tmp_path, monkeypatch):
    new_dir = tmp_path / ".ohverlay"
    legacy_dir = tmp_path / ".zenfish"
    legacy_dir.mkdir()
    legacy_config = legacy_dir / "config.json"
    legacy_config.write_text(
        json.dumps({"modules": {"news": True}, "overlays": {"aurora": True}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(settings_module, "get_app_data_dir", lambda: str(new_dir))
    monkeypatch.setattr(settings_module, "get_legacy_app_data_dir", lambda: str(legacy_dir))

    settings = Settings()

    assert settings.get("modules", "news") is True
    assert settings.get("overlays", "aurora") is True
    assert (new_dir / "config.json").exists()
