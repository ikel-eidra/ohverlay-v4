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
