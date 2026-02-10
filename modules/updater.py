"""
Simple auto-update checker/downloader.
Checks a remote manifest and downloads update installers to a local updates folder.
Does NOT auto-run installers for safety; it notifies user via bubbles.
"""

import os
import time
from typing import Optional
from utils.logger import logger

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AppUpdater:
    def __init__(self, config=None):
        self.enabled = False
        self.current_version = "1.0.0"
        self.support_email = "support@futol.example"
        self.check_interval_hours = 6
        self.manifest_url = ""
        self.channel = "stable"
        self.last_checked = 0.0
        self._pending = None

        self.updates_dir = os.path.join(os.path.expanduser("~"), ".zenfish", "updates")
        os.makedirs(self.updates_dir, exist_ok=True)

        if config:
            self.apply_config(config)

    def apply_config(self, config):
        app_cfg = config.get("app") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(app_cfg, dict):
            return
        self.current_version = str(app_cfg.get("version", self.current_version))
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
                return None
            if not version or not self._is_newer(version):
                return None
            installer_url = str(data.get("installer_url", ""))
            if not installer_url:
                return None
            self._pending = {
                "version": version,
                "installer_url": installer_url,
                "notes": str(data.get("notes", "")),
            }
            logger.info(f"Update available: {version}")
            return self._pending
        except Exception as e:
            logger.warning(f"Update check failed: {e}")
            return None

    def download_pending_update(self) -> Optional[str]:
        if not self._pending or not HAS_REQUESTS:
            return None
        try:
            url = self._pending["installer_url"]
            version = self._pending["version"]
            filename = f"ZenFish-{version}.exe"
            out_path = os.path.join(self.updates_dir, filename)

            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info(f"Update downloaded: {out_path}")
            return out_path
        except Exception as e:
            logger.warning(f"Update download failed: {e}")
            return None
