"""
Overlay Manager - Loads and manages HTML overlay windows via QWebEngineView.
Each overlay runs in its own transparent, always-on-top window.
Interactive overlays (sticky note, chatbox) accept mouse input.
Ambient overlays (aurora, ghost woman) are click-through.
"""

import os
import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QGuiApplication, QColor

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

from utils.logger import logger


# Registry of available overlays
# interactive: True = accepts mouse clicks (sticky note, chatbox)
# interactive: False = click-through (ambient animations)
OVERLAY_REGISTRY = [
    {
        "id": "sticky-note",
        "name": "Sticky Note",
        "file": "sticky-note-overlay.html",
        "category": "productivity",
        "interactive": True,
        "description": "Draggable sticky note with timer and deadline tracking",
    },
    {
        "id": "chatbox",
        "name": "Blue AI Chat",
        "file": "chatbox-overlay.html",
        "category": "productivity",
        "interactive": True,
        "description": "AI chatbox powered by Blue assistant",
    },
    {
        "id": "exam-reviewer",
        "name": "Exam Reviewer",
        "file": "exam-reviewer-overlay.html",
        "category": "productivity",
        "interactive": True,
        "description": "Glowing Q&A cards for exam review with spaced repetition",
    },
    {
        "id": "aurora",
        "name": "Aurora Borealis",
        "file": "aurora.html",
        "category": "ambient",
        "interactive": False,
        "description": "Northern lights dancing across your desktop",
    },
    {
        "id": "fairy-dandelion",
        "name": "Fairy & Dandelion",
        "file": "fairy-dandelion.html",
        "category": "ambient",
        "interactive": False,
        "description": "Wireframe fairy with floating dandelion seeds",
    },
    {
        "id": "manta-ray",
        "name": "Manta Ray",
        "file": "manta-ray-overlay.html",
        "category": "ambient",
        "interactive": False,
        "description": "Graceful wireframe manta ray with neon glow",
    },
    {
        "id": "ghost-woman",
        "name": "Ghost Woman",
        "file": "ghost-woman-overlay.html",
        "category": "ambient",
        "interactive": False,
        "description": "Spectral wireframe woman riding a bicycle",
    },
]


class TransparentWebPage(QWebEnginePage):
    """Web page with transparent background support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundColor(QColor(0, 0, 0, 0))


class OverlayWindow(QMainWindow):
    """A transparent window hosting an HTML overlay."""

    def __init__(self, overlay_info, screen_geometry, parent=None):
        super().__init__(parent)
        self.overlay_id = overlay_info["id"]
        self.overlay_info = overlay_info
        self.interactive = overlay_info.get("interactive", False)

        # Window flags
        flags = (
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        if not self.interactive:
            flags |= Qt.WindowTransparentForInput

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # Cover the full screen
        self.setGeometry(screen_geometry)

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
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)

        # Layout
        central = QWidget(self)
        central.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
        self.setCentralWidget(central)

    def load_html(self, html_path):
        """Load an HTML file into the web view."""
        url = QUrl.fromLocalFile(os.path.abspath(html_path))
        self.web_view.load(url)
        logger.info(f"Overlay '{self.overlay_id}' loaded: {html_path}")


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
                test_file = os.path.join(path, "sticky-note-overlay.html")
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

        try:
            window = OverlayWindow(info, geo)
            window.load_html(html_path)
            window.show()
            self._active[overlay_id] = window

            # Save state
            if self.config:
                self.config.set("overlays", overlay_id, True)

            logger.info(f"Overlay '{info['name']}' opened")
            return True
        except Exception as e:
            logger.error(f"Failed to open overlay '{overlay_id}': {e}")
            return False

    def close_overlay(self, overlay_id):
        """Close a specific overlay."""
        if overlay_id not in self._active:
            return

        window = self._active.pop(overlay_id)
        window.close()

        # Save state
        if self.config:
            self.config.set("overlays", overlay_id, False)

        logger.info(f"Overlay '{overlay_id}' closed")

    def close_all(self):
        """Close all active overlays."""
        for overlay_id in list(self._active.keys()):
            self.close_overlay(overlay_id)

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
