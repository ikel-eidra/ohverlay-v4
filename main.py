"""
Ohverlay - Minimal Nature Baseline
A lightweight desktop overlay runtime for calm, animated nature objects.
"""

import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from ui.tray import SystemTray
from config.settings import Settings
from modules.overlay_manager import OverlayManager
from utils.logger import logger


class OhverlayApp:
    """Main application controller — Minimal Nature Overlay Runtime."""

    def __init__(self):
        # Fix transparent window rendering bugs on Windows with Chromium QWebEngine
        sys.argv.extend([
            "--disable-gpu-compositing",
            "--enable-gpu-rasterization",
            "--ignore-gpu-blocklist",
            "--num-raster-threads=4",
            "--allow-file-access-from-files",
            "--autoplay-policy=no-user-gesture-required"
        ])
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Ohverlay")
        self.app.setOrganizationName("FutolTech")
        self.app.setQuitOnLastWindowClosed(False)

        # Allow Ctrl+C to exit from terminal
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Load configuration
        self.config = Settings()

        # Initialize subsystems
        self._init_overlay_manager()
        self._init_tray()
        self._init_hotkeys()

        logger.info("Ohverlay initialized — Minimal Nature Overlay Runtime ready!")

    def _init_overlay_manager(self):
        """Initialize the HTML overlay system."""
        self.overlay_manager = OverlayManager(config=self.config)
        if self.overlay_manager.available:
            self.overlay_manager.restore_state()
            logger.info("Overlay Manager ready — HTML overlays available")
        else:
            logger.warning("Overlay Manager: QWebEngine not installed — HTML overlays disabled")

    def _init_tray(self):
        """Create system tray icon with settings menu."""
        self.tray = SystemTray(config=self.config, overlay_manager=self.overlay_manager)
        self.tray.signals.toggle_visibility.connect(self._on_toggle_visibility)
        self.tray.signals.quit_app.connect(self._on_quit)
        self.tray.signals.overlay_toggled.connect(self._on_overlay_toggled)
        self.tray.signals.debug_canvas_extents.connect(self._on_debug_canvas_extents)
        self.tray.show()

    def _init_hotkeys(self):
        """Set up global hotkeys."""
        self._hotkey_listener = None
        try:
            from pynput import keyboard

            def on_visibility():
                QTimer.singleShot(0, self._on_toggle_visibility)

            def format_hotkey(hotkey_str):
                parts = hotkey_str.split('+')
                formatted = []
                for p in parts:
                    if p in ('ctrl', 'alt', 'shift', 'cmd'):
                        formatted.append(f"<{p}>")
                    else:
                        formatted.append(p)
                return "+".join(formatted)

            hotkey_vis = format_hotkey(self.config.get('hotkeys', 'toggle_visibility'))

            hotkeys = {
                hotkey_vis: on_visibility,
            }

            self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
            logger.info(f"Global hotkeys registered ({hotkey_vis}=Toggle Overlays)")
        except ImportError:
            logger.warning("pynput not available — global hotkeys disabled")
        except Exception as e:
            logger.warning(f"Hotkey setup failed: {e}")

    # --- Signal handlers ---

    def _on_overlay_toggled(self, overlay_id):
        """Handle overlay toggle from tray menu."""
        result = self.overlay_manager.toggle_overlay(overlay_id)
        self.tray.update_overlay_state(overlay_id, result)

    def _on_toggle_visibility(self):
        """Toggle visibility of all overlays."""
        self.overlay_manager.toggle_all_visibility()

    def _on_quit(self):
        logger.info("Ohverlay shutting down...")
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        self.overlay_manager.close_all()
        self.config.save()
        self.app.quit()

    def run(self):
        """Start the application event loop."""
        return self.app.exec()

    def _on_debug_canvas_extents(self):
        """Inject CSS into all active overlays to visualize their canvas boundaries."""
        logger.info("Executing debug canvas extent script on all overlays")
        js_code = """
        if (!window.__debug_border_active) {
            window.document.body.style.border = "5px solid rgba(255, 0, 0, 0.5)";
            window.document.body.style.backgroundColor = "rgba(255, 0, 0, 0.1)";
            window.document.body.style.boxSizing = "border-box";
            window.__debug_border_active = true;
        } else {
            window.document.body.style.border = "none";
            window.document.body.style.backgroundColor = "transparent";
            window.__debug_border_active = false;
        }
        """
        for win in self.overlay_manager._active.values():
            if win.web_view and win.web_view.page():
                win.web_view.page().runJavaScript(js_code)


def main():
    logger.info("Starting Ohverlay...")
    app = OhverlayApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
