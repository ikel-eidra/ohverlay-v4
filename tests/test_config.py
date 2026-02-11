from config.settings import Settings, DEFAULT_CONFIG


def test_default_config_structure():
    assert "fish" in DEFAULT_CONFIG
    assert "sanctuary" in DEFAULT_CONFIG
    assert "modules" in DEFAULT_CONFIG
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


def test_settings_get_set():
    settings = Settings()
    settings.set("fish", "primary_color", [255, 0, 0])
    assert settings.get("fish", "primary_color") == [255, 0, 0]


def test_default_betta_palette_present():
    assert DEFAULT_CONFIG["fish"]["betta_palette"] == "nemo_galaxy"


def test_fish_visual_tuning_defaults_present():
    assert DEFAULT_CONFIG["fish"]["silhouette_strength"] == 1.0
    assert DEFAULT_CONFIG["fish"]["eye_tracking_strength"] == 0.75
    assert DEFAULT_CONFIG["fish"]["eye_tracking_damping"] == 0.18


def test_app_prelaunch_defaults_present():
    assert DEFAULT_CONFIG["app"]["public_website_enabled"] is False
    assert DEFAULT_CONFIG["app"]["website_release_stage"] == "private_prelaunch"
