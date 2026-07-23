"""
Overlay Manager - Loads and manages HTML overlay windows via QWebEngineView.
Each overlay runs in its own transparent, always-on-top window.
"""

import os
import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QGuiApplication, QColor

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

from utils.logger import logger


OVERLAY_REGISTRY = [
    {
        "id": "nature_world",
        "name": "Unified Nature World",
        "file": "nature-world-overlay.html",
        "category": "ambient",
        "description": "Unified single-canvas nature world with dragonflies, fireflies, and dandelions",
    },
    {
        "id": "fireflies",
        "name": "Fireflies",
        "file": "fireflies-overlay.html",
        "category": "ambient",
        "description": "Six realistic fireflies flying and flashing independently",
    },
    {
        "id": "dandelions",
        "name": "Dandelion Seeds",
        "file": "dandelions-overlay.html",
        "category": "ambient",
        "description": "Dandelion seeds floating and drifting",
    },
    {
        "id": "dragonflies",
        "name": "Realistic Dragonflies",
        "file": "dragonflies-overlay.html",
        "category": "ambient",
        "description": "Two realistic dragonflies hovering and darting",
    },
]


class TransparentWebPage(QWebEnginePage):
    """Web page with transparent background support and console log redirect."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundColor(QColor(0, 0, 0, 0))

    def javaScriptConsoleMessage(self, level, message, lineID, sourceID):
        logger.info(f"JS [Level {level}]: {message} (Line: {lineID}, Source: {sourceID})")


class OverlayWindow(QMainWindow):
    """A transparent window hosting an HTML overlay."""

    def __init__(self, overlay_info, screen_geometry, parent=None):
        super().__init__(parent)
        self.overlay_id = overlay_info["id"]
        self.overlay_info = overlay_info
        self._intended_geometry = screen_geometry

        flags = (
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.web_view = QWebEngineView(self)
        self.web_page = TransparentWebPage(self.web_view)
        self.web_view.setPage(self.web_page)

        self.web_view.setStyleSheet("background: transparent;")
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)

        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)

        central = QWidget(self)
        central.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.web_view)
        self.setCentralWidget(central)

        self.setGeometry(screen_geometry)
        self.setFixedSize(screen_geometry.width(), screen_geometry.height())
        self.move(screen_geometry.topLeft())

    def load_local_html(self, relative_path, scale=1.0, count=None, extra_params=None):
        file_path = os.path.abspath(relative_path)
        if not os.path.exists(file_path):
            logger.error(f"HTML overlay file not found: {file_path}")
            return False

        url = QUrl.fromLocalFile(file_path)
        url_string = url.toString()
        params = []
        if scale != 1.0:
            params.append(f"scale={scale}")
        if count is not None:
            params.append(f"count={count}")
        if extra_params:
            for k, v in extra_params.items():
                params.append(f"{k}={v}")
        if params:
            url_string += "?" + "&".join(params)
        self.web_view.load(QUrl(url_string))
        logger.info(f"Loading overlay {self.overlay_id} from {file_path} (scale={scale}, count={count})")
        return True


class OverlayManager:
    """Manages creation, visibility, and multi-monitor bounds of HTML overlays."""

    def __init__(self, config=None):
        self.config = config
        self.available = HAS_WEBENGINE
        self._active = {}
        self._global_visible = True

    def get_registry(self):
        return OVERLAY_REGISTRY

    def _get_total_virtual_geometry(self):
        """Calculate the total bounding box spanning all monitors."""
        screens = QGuiApplication.screens()
        if not screens:
            return None
            
        min_x = min(s.geometry().x() for s in screens)
        min_y = min(s.geometry().y() for s in screens)
        max_right = max(s.geometry().right() for s in screens)
        max_bottom = max(s.geometry().bottom() for s in screens)
        
        from PySide6.QtCore import QRect
        return QRect(min_x, min_y, max_right - min_x + 1, max_bottom - min_y + 1)

    def reload_nature_world(self):
        """Reload or open the unified nature world window with current config parameters."""
        if not self.available:
            return False

        ff_active = bool(self.config.get("overlays", "fireflies")) if self.config else True
        df_active = bool(self.config.get("overlays", "dragonflies")) if self.config else True
        dd_active = bool(self.config.get("overlays", "dandelions")) if self.config else True

        if not (ff_active or df_active or dd_active):
            if "nature_world" in self._active:
                win = self._active.pop("nature_world")
                win.close()
                win.deleteLater()
            return True

        extra_params = {
            "fireflies_active": "true" if ff_active else "false",
            "dragonflies_active": "true" if df_active else "false",
            "dandelions_active": "true" if dd_active else "false",
            "fireflies_count": self.config.get("overlays", "fireflies_count") or 6,
            "dragonflies_count": self.config.get("overlays", "dragonflies_count") or 2,
            "dandelions_count": self.config.get("overlays", "dandelions_count") or 3,
            "fireflies_scale": self.config.get("overlays", "fireflies_scale") or 1.0,
            "dragonflies_scale": self.config.get("overlays", "dragonflies_scale") or 1.0,
            "dandelions_scale": self.config.get("overlays", "dandelions_scale") or 1.0,
            "physics_preset": self.config.get("nature", "physics_preset") or "lively",
            "interaction_strength": self.config.get("nature", "interaction_strength") or 1.0,
        }

        info = next((o for o in OVERLAY_REGISTRY if o["id"] == "nature_world"), None)
        geometry = self._get_total_virtual_geometry()
        if not info or not geometry:
            return False

        if "nature_world" not in self._active:
            win = OverlayWindow(info, geometry)
            self._active["nature_world"] = win
        else:
            win = self._active["nature_world"]

        win.load_local_html(info["file"], extra_params=extra_params)
        if self._global_visible:
            win.show()
            win.setWindowFlags(win.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowTransparentForInput)
            win.show()
        return True

    def open_overlay(self, overlay_id, save_state=True):
        if not self.available:
            return False

        if save_state and self.config:
            self.config.set("overlays", overlay_id, True)

        if overlay_id in ["fireflies", "dragonflies", "dandelions", "nature_world"]:
            return self.reload_nature_world()

        if overlay_id in self._active:
            self._active[overlay_id].show()
            return True

        info = next((o for o in OVERLAY_REGISTRY if o["id"] == overlay_id), None)
        if not info:
            logger.error(f"Unknown overlay ID: {overlay_id}")
            return False

        geometry = self._get_total_virtual_geometry()
        if not geometry:
            return False

        win = OverlayWindow(info, geometry)
        if win.load_local_html(info["file"]):
            self._active[overlay_id] = win
            if self._global_visible:
                win.show()
                win.setWindowFlags(win.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowTransparentForInput)
                win.show()
            return True
        return False

    def close_overlay(self, overlay_id, save_state=True):
        if save_state and self.config:
            self.config.set("overlays", overlay_id, False)

        if overlay_id in ["fireflies", "dragonflies", "dandelions", "nature_world"]:
            return self.reload_nature_world()

        if overlay_id in self._active:
            win = self._active.pop(overlay_id)
            win.close()
            win.deleteLater()
            logger.info(f"Closed overlay: {overlay_id}")

    def toggle_overlay(self, overlay_id):
        if self.is_active(overlay_id):
            self.close_overlay(overlay_id)
            return False
        else:
            self.open_overlay(overlay_id)
            return True

    def is_active(self, overlay_id):
        if overlay_id in ["fireflies", "dragonflies", "dandelions", "nature_world"]:
            if "nature_world" in self._active:
                if self.config:
                    return bool(self.config.get("overlays", overlay_id))
                return True
            return False
        return overlay_id in self._active

    def get_active_ids(self):
        return list(self._active.keys())

    def toggle_all_visibility(self):
        self._global_visible = not self._global_visible
        for win in self._active.values():
            if self._global_visible:
                win.show()
            else:
                win.hide()
        return self._global_visible

    def restore_state(self):
        if not self.config or not self.available:
            return
        self.reload_nature_world()

    def close_all(self):
        for win in list(self._active.values()):
            win.close()
            win.deleteLater()
        self._active.clear()
