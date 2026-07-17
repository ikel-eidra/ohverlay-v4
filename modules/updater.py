"""
Simple auto-update checker/downloader.
Checks a remote manifest and downloads update installers to a local updates folder.
Does NOT auto-run installers for safety; it notifies user via bubbles.
"""

import hashlib
import os
import time
from typing import Optional
from config.settings import DEFAULT_CONFIG, get_updates_dir
from utils.logger import logger

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AppUpdater:
    def __init__(self, config=None):
        self.enabled = False
        self.current_version = str(DEFAULT_CONFIG.get("app", {}).get("version", "1.0.0"))
        self.support_email = "support@ohverlay.com"
        self.check_interval_hours = 6
        self.manifest_url = ""
        self.channel = "stable"
        self.last_checked = 0.0
        self._pending = None

        self.updates_dir = get_updates_dir()
        os.makedirs(self.updates_dir, exist_ok=True)

        if config:
            self.apply_config(config)

    @staticmethod
    def _parse_version(version):
        parts = []
        for chunk in str(version).split('.'):
            try:
                parts.append(int(chunk))
            except Exception:
                parts.append(0)
        return parts

    @classmethod
    def _pick_current_version(cls, configured_version: str) -> str:
        bundled_version = str(DEFAULT_CONFIG.get("app", {}).get("version", "1.0.0"))
        return configured_version if cls._parse_version(configured_version) >= cls._parse_version(bundled_version) else bundled_version

    def _clear_pending(self):
        self._pending = None

    def apply_config(self, config):
        app_cfg = config.get("app") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(app_cfg, dict):
            return
        configured_version = str(app_cfg.get("version", self.current_version))
        self.current_version = self._pick_current_version(configured_version)
        self.support_email = str(app_cfg.get("support_email", self.support_email))
        self.enabled = bool(app_cfg.get("auto_update_enabled", True))
        self.check_interval_hours = max(1, int(app_cfg.get("update_check_hours", self.check_interval_hours) or 6))
        self.manifest_url = str(app_cfg.get("update_manifest_url", "") or "")
        self.channel = str(app_cfg.get("update_channel", self.channel) or "stable")

    def _is_newer(self, candidate: str) -> bool:
        def parse(v):
            out=[]
            for x in str(v).split('.'):
                try: out.append(int(x))
                except Exception: out.append(0)
            return out
        a=parse(candidate); b=parse(self.current_version)
        l=max(len(a),len(b)); a+= [0]*(l-len(a)); b+=[0]*(l-len(b))
        return a>b

    def check_for_updates(self, force=False):
        if not self.enabled or not self.manifest_url or not HAS_REQUESTS:
            self._clear_pending()
            return None
        now = time.time()
        if not force and now - self.last_checked < self.check_interval_hours * 3600:
            return None
        self.last_checked = now

        try:
            resp = requests.get(self.manifest_url, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            version = str(data.get("version", ""))
            channel = str(data.get("channel", self.channel))
            if channel != self.channel:
                self._clear_pending()
                return None
            if not version or not self._is_newer(version):
                self._clear_pending()
                return None
            installer_url = str(data.get("installer_url", ""))
            if not installer_url:
                self._clear_pending()
                return None
            self._pending = {
                "version": version,
                "installer_url": installer_url,
                "notes": str(data.get("notes", "")),
                "installer_sha256": str(data.get("installer_sha256") or data.get("sha256") or "").strip().lower(),
            }
            logger.info(f"Update available: {version}")
            return self._pending
        except Exception as e:
            self._clear_pending()
            logger.warning(f"Update check failed: {e}")
            return None

    def _verify_download(self, path: str) -> bool:
        if not self._pending:
            return False

        expected_hash = (self._pending.get("installer_sha256") or "").strip().lower()
        if not expected_hash:
            return True

        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        actual_hash = digest.hexdigest().lower()
        if actual_hash == expected_hash:
            return True

        logger.warning(
            f"Update checksum mismatch: expected {expected_hash}, got {actual_hash}"
        )
        return False

    def download_pending_update(self) -> Optional[str]:
        if not self._pending or not HAS_REQUESTS:
            return None
        try:
            url = self._pending["installer_url"]
            version = self._pending["version"]
            filename = f"Ohverlay-{version}.exe"
            out_path = os.path.join(self.updates_dir, filename)

            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            if not self._verify_download(out_path):
                try:
                    os.remove(out_path)
                except OSError:
                    pass
                return None

            logger.info(f"Update downloaded: {out_path}")
            return out_path
        except Exception as e:
            logger.warning(f"Update download failed: {e}")
            return None
