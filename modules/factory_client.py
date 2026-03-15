"""
Factory Client - Ohverlay Desktop App
=======================================
Connects the desktop app to the Ohverlay Factory at ohverlay.com.

Features:
- Fetch overlay catalog and daily drops
- Check for app updates
- Sync Blue AI memory (optional)
- Download new overlays on demand
- Submit anonymous analytics
"""

import os
import time
import json
import threading
from typing import Optional, List
from utils.logger import logger

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class FactoryClient:
    """Desktop app client for the Ohverlay Factory API."""

    def __init__(self, config=None):
        self.factory_url = "https://ohverlay.com"
        self.api_base = f"{self.factory_url}/api/v1"
        self.user_id = ""
        self.api_key = ""
        self.app_version = "4.0.0"
        self.enabled = True
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._overlay_dir = os.path.join(os.path.expanduser("~"), ".ohverlay", "overlays")
        os.makedirs(self._overlay_dir, exist_ok=True)

        if config:
            self._load_config(config)

    def _load_config(self, config):
        app_cfg = config.get("app") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(app_cfg, dict):
            return
        self.factory_url = str(app_cfg.get("factory_url", self.factory_url) or self.factory_url)
        self.api_base = f"{self.factory_url}/api/v1"
        self.app_version = str(app_cfg.get("version", self.app_version))
        self.enabled = bool(app_cfg.get("factory_enabled", True))

        factory_cfg = config.get("factory") if hasattr(config, "get") and callable(config.get) else {}
        if isinstance(factory_cfg, dict):
            self.user_id = str(factory_cfg.get("user_id", "") or "")
            self.api_key = str(factory_cfg.get("api_key", "") or "")

    def _get(self, path, params=None, timeout=10):
        """Make a GET request to the factory API."""
        if not HAS_REQUESTS or not self.enabled:
            return None

        # Check cache
        cache_key = f"{path}:{json.dumps(params or {}, sort_keys=True)}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["time"] < self._cache_ttl:
                return cached["data"]

        try:
            headers = {"User-Agent": f"OhverlayDesktop/{self.app_version}"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            resp = requests.get(
                f"{self.api_base}{path}",
                params=params,
                headers=headers,
                timeout=timeout,
            )

            if resp.status_code == 200:
                data = resp.json()
                self._cache[cache_key] = {"time": time.time(), "data": data}
                return data

        except Exception as e:
            logger.debug(f"Factory API error ({path}): {e}")

        return None

    # ─── Overlay Catalog ───

    def get_overlay_catalog(self, category=None):
        """Fetch the full overlay catalog from the factory."""
        params = {}
        if category:
            params["category"] = category
        return self._get("/overlays", params) or []

    def get_daily_overlays(self):
        """Fetch today's featured overlays."""
        return self._get("/overlays/daily") or {"overlays": []}

    def download_overlay(self, overlay_id):
        """Download an overlay HTML file to local storage."""
        if not HAS_REQUESTS:
            return None

        info = self._get(f"/overlays/{overlay_id}")
        if not info or "download_url" not in info:
            return None

        try:
            resp = requests.get(info["download_url"], timeout=30)
            if resp.status_code == 200:
                filepath = os.path.join(self._overlay_dir, f"{overlay_id}.html")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                logger.info(f"Downloaded overlay: {overlay_id} → {filepath}")
                return filepath
        except Exception as e:
            logger.warning(f"Overlay download failed: {e}")

        return None

    # ─── Updates ───

    def check_for_updates(self):
        """Check the factory for app updates."""
        manifest = self._get("/updates/manifest")
        if not manifest:
            return None

        remote_version = manifest.get("version", "")
        if not remote_version:
            return None

        # Simple version comparison
        def parse_ver(v):
            parts = []
            for x in str(v).split("."):
                try:
                    parts.append(int(x))
                except ValueError:
                    parts.append(0)
            return parts

        if parse_ver(remote_version) > parse_ver(self.app_version):
            return manifest

        return None

    # ─── News / Weather / Tickers ───

    def get_news(self, topic="technology", limit=5):
        """Fetch curated news from the factory."""
        return self._get("/news", {"topic": topic, "limit": limit})

    def get_weather(self, city="Manila"):
        """Fetch weather from the factory."""
        return self._get("/weather", {"city": city})

    def get_tickers(self, coins="bitcoin,ethereum"):
        """Fetch crypto prices from the factory."""
        return self._get("/tickers", {"coins": coins})

    # ─── Blue AI (server-side chat for web parity) ───

    def blue_chat(self, message, context=""):
        """Send a chat message to factory-hosted Blue AI."""
        if not HAS_REQUESTS or not self.enabled:
            return None

        try:
            resp = requests.post(
                f"{self.api_base}/blue/chat",
                json={
                    "message": message,
                    "user_id": self.user_id,
                    "context": context,
                },
                headers={"User-Agent": f"OhverlayDesktop/{self.app_version}"},
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

        return None

    # ─── Analytics (anonymous, opt-in) ───

    def send_event(self, event_type, data=None):
        """Send anonymous analytics event to factory."""
        if not HAS_REQUESTS or not self.enabled:
            return

        def _send():
            try:
                requests.post(
                    f"{self.api_base}/analytics/event",
                    json={
                        "event_type": event_type,
                        "user_id": self.user_id,
                        "data": data or {},
                        "app_version": self.app_version,
                    },
                    headers={"User-Agent": f"OhverlayDesktop/{self.app_version}"},
                    timeout=5,
                )
            except Exception:
                pass

        # Fire and forget
        threading.Thread(target=_send, daemon=True).start()

    # ─── Factory Health ───

    def is_factory_online(self):
        """Check if the factory is reachable."""
        result = self._get("/health")
        return result is not None and result.get("status") == "alive"
