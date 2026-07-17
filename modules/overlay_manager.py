"""
Overlay Manager - Loads and manages HTML overlay windows via QWebEngineView.
Each overlay runs in its own transparent, always-on-top window.
Interactive overlays (sticky note, chatbox) accept mouse input.
Ambient overlays (aurora, ghost woman) are click-through.
"""

import os
import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QUrl, QSize, QPoint
from PySide6.QtGui import QGuiApplication, QColor

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

from utils.logger import logger


# Registry of available overlays
# interactive: True = accepts mouse clicks
# interactive: False = click-through (ambient animations)
OVERLAY_REGISTRY = [
    {
        "id": "ecosystem",
        "name": "Ecosystem (Unified Nature)",
        "file": "ecosystem-overlay.html",
        "category": "ambient",
        "interactive": False,
        "description": "Unified physics engine where dragonflies, dandelions, fireflies, and hornwort interact",
    },
    {
        "id": "fireflies",
        "name": "Fireflies",
        "file": "fireflies-overlay.html",
        "category": "ambient",
        "interactive": False,
        "description": "Six realistic fireflies flying and flashing independently",
    },
    {
        "id": "volumetric-clouds",
        "name": "Volumetric Clouds",
        "file": "volumetric-clouds.html",
        "category": "ambient",
        "interactive": False,
        "description": "Slow volumetric clouds crossing the upper part of the screen",
    },
    {
        "id": "paper-lanterns",
        "name": "Paper Lanterns",
        "file": "paper-lanterns-overlay.html",
        "category": "ambient",
        "interactive": False,
        "description": "Softly glowing paper lanterns drifting upwards in an invisible wind",
    },

    {
        "id": "dandelions",
        "name": "Dandelion Seeds",
        "file": "dandelion-overlay.html",
        "category": "ambient",
        "interactive": False,
        "description": "Dandelion seeds floating and drifting",
    },
    {
        "id": "dragonflies",
        "name": "Realistic Dragonflies",
        "file": "dragonflies-overlay.html",
        "category": "ambient",
        "interactive": False,
        "description": "Two realistic dragonflies hovering and darting",
    },

    {
        "id": "screensaver-nature",
        "name": "Nature Screensaver (Bahay Kubo)",
        "file": "screensaver-overlay.html",
        "category": "screensaver",
        "interactive": False,
        "description": "Continuous rain, plants, and a cozy Bahay Kubo triggered on idle.",
    },
]


class TransparentWebPage(QWebEnginePage):
    """Web page with transparent background support and console log redirect."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundColor(QColor(0, 0, 0, 0))

    def javaScriptConsoleMessage(self, level, message, lineID, sourceID):
        logger.info(f"JS [Level {level}]: {message} (Line: {lineID}, Source: {sourceID})")
        if "OHVERLAY_ACTION:CLOSE_CHAT" in message:
            view = self.view()
            if view:
                window = view.parent()
                if window and hasattr(window, "set_interactive"):
                    window.set_interactive(False, force=True)


class OverlayWindow(QMainWindow):
    """A transparent window hosting an HTML overlay."""

    def __init__(self, overlay_info, screen_geometry, parent=None):
        super().__init__(parent)
        self.overlay_id = overlay_info["id"]
        self.overlay_info = overlay_info
        self.interactive = overlay_info.get("interactive", False)
        self._intended_geometry = screen_geometry  # Store for re-application

        # Window flags
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

        # Web view
        self.web_view = QWebEngineView(self)
        self.web_page = TransparentWebPage(self.web_view)
        self.web_view.setPage(self.web_page)

        # Transparent web view
        self.web_view.setStyleSheet("background: transparent;")
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)

        # Enable web settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)

        # Layout
        central = QWidget(self)
        central.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
        self.setCentralWidget(central)

        # Cover the full screen (set AFTER layout so geometry sticks)
        self.setGeometry(screen_geometry)
        self.setFixedSize(screen_geometry.size())

    def showEvent(self, event):
        """Force correct geometry every time the window is shown.
        Windows sometimes resets Tool window geometry to a tiny default."""
        super().showEvent(event)
        if self._intended_geometry:
            self.setGeometry(self._intended_geometry)
            self.setFixedSize(self._intended_geometry.size())

    def load_html(self, html_path, query_params=None):
        """Load an HTML file into the web view."""
        url = QUrl.fromLocalFile(os.path.abspath(html_path))
        if query_params:
            from PySide6.QtCore import QUrlQuery
            query = QUrlQuery()
            for k, v in query_params.items():
                query.addQueryItem(k, str(v))
            url.setQuery(query)
        self.web_view.load(url)
        logger.info(f"Overlay '{self.overlay_id}' loaded: {html_path}")

    def set_interactive(self, interactive_state, force=False):
        """Toggle input passthrough at runtime and refresh window flags."""
        if not force and not self.interactive and interactive_state:
            return  # Cannot make an ambient overlay interactive

        flags = self.windowFlags()
        if interactive_state:
            flags &= ~Qt.WindowTransparentForInput
        else:
            flags |= Qt.WindowTransparentForInput

        self.setWindowFlags(flags)
        self.show()  # Required to apply new window flags on Windows
        self.raise_() # Force Z-order on top of other topmost windows
        logger.info(f"Overlay '{self.overlay_id}' interactivity set to: {interactive_state} (force={force})")


class OverlayManager:
    """Manages loading, toggling, and lifecycle of HTML overlay windows."""

    def __init__(self, config=None):
        self.config = config
        self._active = {}  # overlay_id -> OverlayWindow
        self._registry = {ov["id"]: ov for ov in OVERLAY_REGISTRY}
        self._base_path = self._find_base_path()

        if not HAS_WEBENGINE:
            logger.warning(
                "PySide6-WebEngine not installed. HTML overlays disabled. "
                "Install with: pip install PySide6-WebEngine"
            )

    def _find_base_path(self):
        """Find the directory containing HTML overlay files."""
        # When running from source
        candidates = [
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # project root
            os.path.dirname(sys.executable),  # PyInstaller bundle
            getattr(sys, '_MEIPASS', ''),  # PyInstaller temp dir
            os.getcwd(),
        ]
        for path in candidates:
            if path and os.path.isdir(path):
                # Check if at least one overlay file exists here
                test_file = os.path.join(path, "tetra-fish-overlay.html")
                if os.path.isfile(test_file):
                    return path
        # Fallback to project root
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @property
    def available(self):
        """Check if overlay system is available."""
        return HAS_WEBENGINE

    def get_registry(self):
        """Return list of all available overlays."""
        return list(OVERLAY_REGISTRY)

    def is_active(self, overlay_id):
        """Check if an overlay is currently active."""
        return overlay_id in self._active

    def get_active_ids(self):
        """Return list of active overlay IDs."""
        return list(self._active.keys())

    def toggle_overlay(self, overlay_id):
        """Toggle an overlay on or off. Returns new state (True=on, False=off)."""
        if overlay_id in self._active:
            self.close_overlay(overlay_id)
            return False
        else:
            return self.open_overlay(overlay_id)

    def toggle_interactivity(self):
        """Toggle interactivity state of all active interactive overlays."""
        # Find if any overlay is currently interactive (not transparent for input)
        is_currently_interactive = False
        for window in self._active.values():
            if window.interactive and not (window.windowFlags() & Qt.WindowTransparentForInput):
                is_currently_interactive = True
                break

        # Flip the state
        new_state = not is_currently_interactive
        
        for window in self._active.values():
            if window.interactive:
                window.set_interactive(new_state)
        
        return new_state

    def open_overlay(self, overlay_id):
        """Open an overlay. Returns True if successful."""
        if not HAS_WEBENGINE:
            logger.warning(f"Cannot open overlay '{overlay_id}': QWebEngine not available")
            return False

        if overlay_id in self._active:
            logger.info(f"Overlay '{overlay_id}' already active")
            return True

        info = self._registry.get(overlay_id)
        if not info:
            logger.warning(f"Unknown overlay: {overlay_id}")
            return False

        html_path = os.path.join(self._base_path, info["file"])
        if not os.path.isfile(html_path):
            logger.warning(f"Overlay file not found: {html_path}")
            return False

        # Use primary screen
        screen = QGuiApplication.primaryScreen()
        if not screen:
            logger.warning("No screen available")
            return False

        geo = screen.geometry()

        query_params = {}
        if self.config:
            scale = self.config.get("overlays", f"{overlay_id}_scale")
            if scale is None:
                scale = self.config.get("overlays", "global_scale")
            if scale is not None:
                query_params["scale"] = scale

        if overlay_id in ("neon-tetra", "glass-fish", "yellow-boxfish") and self.config:
            school_size = self.config.get("fish", "school_size")
            size_preset = self.config.get("fish", "size")
            speed_preset = self.config.get("fish", "speed") or "normal"
            behavior_preset = self.config.get("fish", "behavior") or "schooling"
            opacity = self.config.get("fish", "opacity")

            # PPI display density calculation
            try:
                ppi = screen.physicalDotsPerInch()
                if ppi < 10 or ppi > 500:
                    ppi = 96.0
            except Exception:
                ppi = 96.0

            query_params = {}
            if school_size: query_params["school_size"] = school_size
            if size_preset: query_params["size"] = size_preset
            query_params["speed"] = speed_preset
            query_params["behavior"] = behavior_preset
            query_params["ppi"] = ppi
            if opacity is not None:
                query_params["opacity"] = opacity

        try:
            window = OverlayWindow(info, geo)
            window.load_html(html_path, query_params)
            window.show()
            window.raise_()  # Force Z-order to front
            self._active[overlay_id] = window

            # Save state
            if self.config:
                self.config.set("overlays", overlay_id, True)

            logger.info(f"Overlay '{info['name']}' opened")
            return True
        except Exception as e:
            logger.error(f"Failed to open overlay '{overlay_id}': {e}")
            return False

    def close_overlay(self, overlay_id, save_state=True):
        """Close a specific overlay."""
        if overlay_id not in self._active:
            return

        window = self._active.pop(overlay_id)
        window.close()

        # Save state
        if save_state and self.config:
            self.config.set("overlays", overlay_id, False)

        logger.info(f"Overlay '{overlay_id}' closed")

    def close_all(self):
        """Close all active overlays without saving state as disabled (used on shutdown)."""
        for overlay_id in list(self._active.keys()):
            self.close_overlay(overlay_id, save_state=False)

    def restore_state(self):
        """Restore previously active overlays from config."""
        if not self.config or not HAS_WEBENGINE:
            return

        overlays_config = self.config.get("overlays")
        if not isinstance(overlays_config, dict):
            return

        for overlay_id, enabled in overlays_config.items():
            if enabled and overlay_id in self._registry:
                self.open_overlay(overlay_id)

    def toggle_all_visibility(self):
        """Toggle visibility of all active overlays."""
        for window in self._active.values():
            if window.isVisible():
                window.hide()
            else:
                window.show()
                window.raise_()

    def start_feeding_mode(self):
        """Temporarily enable overlay interactivity and trigger the custom spoon feeding mode in active fish overlays."""
        logger.info("Entering feeding mode: enabling window interactivity and spawning feeding spoon...")
        for overlay_id, window in self._active.items():
            if overlay_id in ("neon-tetra", "glass-fish", "yellow-boxfish"):
                window.set_interactive(True, force=True)
                window.web_view.page().runJavaScript(
                    "if (typeof window.startFeedingMode === 'function') window.startFeedingMode();"
                )

        # Awtomatikong ibalik sa click-through after 8 seconds (gives plenty of time to feed and watch)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(8000, self.stop_feeding_mode)

    def stop_feeding_mode(self):
        """Restore active fish overlays to transparent click-through mode."""
        logger.info("Exiting feeding mode: restoring window click-through...")
        for overlay_id, window in self._active.items():
            if overlay_id in ("neon-tetra", "glass-fish", "yellow-boxfish"):
                window.set_interactive(False, force=True)

    def chat_with_bubbles(self):
        """Temporarily enable overlay interactivity and show the Bubbles chatbox."""
        logger.info("Opening Bubbles chat: temporarily enabling window interactivity...")
        window = self._active.get("neon-tetra")
        if window:
            window.set_interactive(True, force=True)
            window.activateWindow()
            window.raise_()
            window.web_view.setFocus()
            window.web_view.page().runJavaScript(
                "if (typeof window.openChatFromTray === 'function') window.openChatFromTray();"
            )
