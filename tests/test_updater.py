import hashlib

import modules.updater as updater_module
from config.settings import DEFAULT_CONFIG
from modules.updater import AppUpdater


class FakeConfig:
    def __init__(self, app_cfg):
        self._app_cfg = app_cfg

    def get(self, section, key=None):
        if section == "app" and key is None:
            return self._app_cfg
        return None


class FakeManifestResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeDownloadResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=8192):
        for idx in range(0, len(self.payload), chunk_size):
            yield self.payload[idx:idx + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_updater_prefers_bundled_version_when_config_is_stale(tmp_path, monkeypatch):
    monkeypatch.setenv("OHVERLAY_HOME", str(tmp_path / ".ohverlay"))

    stale_version = "3.9.0"
    config = FakeConfig({
        "version": stale_version,
        "support_email": "support@ohverlay.com",
        "auto_update_enabled": True,
        "update_check_hours": 6,
        "update_manifest_url": "https://example.com/manifest.json",
        "update_channel": "stable",
    })

    updater = AppUpdater(config=config)

    assert updater.current_version == DEFAULT_CONFIG["app"]["version"]


def test_check_for_updates_clears_stale_pending_on_channel_mismatch(tmp_path, monkeypatch):
    monkeypatch.setenv("OHVERLAY_HOME", str(tmp_path / ".ohverlay"))

    config = FakeConfig({
        "version": DEFAULT_CONFIG["app"]["version"],
        "support_email": "support@ohverlay.com",
        "auto_update_enabled": True,
        "update_check_hours": 6,
        "update_manifest_url": "https://example.com/manifest.json",
        "update_channel": "stable",
    })

    updater = AppUpdater(config=config)
    updater._pending = {"version": "9.9.9", "installer_url": "https://stale.example.com/app.exe"}

    class FakeRequests:
        @staticmethod
        def get(url, timeout=8):
            return FakeManifestResponse({
                "version": "4.1.0",
                "channel": "beta",
                "installer_url": "https://example.com/Ohverlay.exe",
            })

    monkeypatch.setattr(updater_module, "HAS_REQUESTS", True)
    monkeypatch.setattr(updater_module, "requests", FakeRequests)

    assert updater.check_for_updates(force=True) is None
    assert updater._pending is None


def test_download_pending_update_verifies_sha256_and_keeps_valid_file(tmp_path, monkeypatch):
    monkeypatch.setenv("OHVERLAY_HOME", str(tmp_path / ".ohverlay"))

    updater = AppUpdater()
    payload = b"ohverlay-update-binary"
    expected_sha256 = hashlib.sha256(payload).hexdigest()
    updater._pending = {
        "version": "4.1.0",
        "installer_url": "https://example.com/Ohverlay.exe",
        "installer_sha256": expected_sha256,
    }

    class FakeRequests:
        @staticmethod
        def get(url, stream=True, timeout=15):
            return FakeDownloadResponse(payload)

    monkeypatch.setattr(updater_module, "HAS_REQUESTS", True)
    monkeypatch.setattr(updater_module, "requests", FakeRequests)

    out_path = updater.download_pending_update()

    assert out_path is not None
    assert tmp_path.joinpath(".ohverlay", "updates", "Ohverlay-4.1.0.exe").exists()


def test_download_pending_update_rejects_bad_sha256_and_removes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("OHVERLAY_HOME", str(tmp_path / ".ohverlay"))

    updater = AppUpdater()
    updater._pending = {
        "version": "4.1.0",
        "installer_url": "https://example.com/Ohverlay.exe",
        "installer_sha256": "deadbeef",
    }

    class FakeRequests:
        @staticmethod
        def get(url, stream=True, timeout=15):
            return FakeDownloadResponse(b"wrong-binary")

    monkeypatch.setattr(updater_module, "HAS_REQUESTS", True)
    monkeypatch.setattr(updater_module, "requests", FakeRequests)

    out_path = updater.download_pending_update()

    assert out_path is None
    assert not tmp_path.joinpath(".ohverlay", "updates", "Ohverlay-4.1.0.exe").exists()
