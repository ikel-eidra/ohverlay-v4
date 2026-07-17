"""
OHVERLAY V4.0 - Desktop Overlay Platform
A professional desktop overlay system that puts everything on your screen.
Overlays include: Sticky Notes, AI Chatbox (Blue), Exam Reviewer,
ambient animations, and more.

By Futol Ethical Technology Ecosystems
"""

import sys
import signal
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QGuiApplication, QCursor, QIcon, QAction
from PySide6.QtCore import QTimer, QBuffer, QByteArray, QThread, Qt

from modules.inactivity_tracker import InactivityTracker

from engine.brain import BehavioralReactor
from engine.aquarium import MonitorManager
from engine.sanctuary import SanctuaryEngine
from engine.llm_brain import LLMBrain
from ui.bubbles import BubbleSystem
from ui.tray import SystemTray
from config.settings import Settings
from modules.health import HealthModule
from modules.love_notes import LoveNotesModule
from modules.schedule import ScheduleModule
from modules.news import NewsModule
from modules.telegram_bridge import TelegramBridge
from modules.webhook_server import WebhookServer
from modules.updater import AppUpdater
from modules.overlay_manager import OverlayManager
from utils.logger import logger


class OhverlayApp:
    """Main application controller — Overlay Platform."""

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
        self.app.setApplicationName("Ohverlay v4.0")
        self.app.setOrganizationName("Futol Ethical Technology Ecosystems")
        self.app.setOrganizationDomain("futol-ethical-technology-ecosystems.local")
        self.app.setQuitOnLastWindowClosed(False)

        # Allow Ctrl+C to exit from terminal
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Load configuration
        self.config = Settings()

        # Initialize subsystems (order matters)
        self._init_monitors()
        self._init_llm_brain()
        self._init_messaging()
        self._init_updater()
        self._init_brain()
        self._init_modules()
        self._init_overlay_manager()
        self._init_tray()
        self._init_hotkeys()
        self._init_main_loop()
        self._init_blue_vision_bridge()

        # Update tray status
        self._update_tray_status()

        logger.info("OHVERLAY V4.0 initialized — Desktop Overlay Platform ready!")

    def _init_monitors(self):
        """Detect monitors."""
        self.monitor_manager = MonitorManager()
        self.total_bounds = self.monitor_manager.get_total_bounds_tuple()

    def _init_llm_brain(self):
        """Initialize the LLM Brain for intelligent orchestration."""
        self.llm_brain = LLMBrain(config=self.config)
        if self.llm_brain.is_available:
            logger.info(f"LLM Brain active: {self.llm_brain.provider} ({self.llm_brain.model})")
        else:
            logger.info("LLM Brain: no API key configured — using static fallback messages")

    def _init_messaging(self):
        """Initialize Telegram bridge and webhook server."""
        self.telegram_bridge = TelegramBridge(config=self.config)
        if self.telegram_bridge.enabled:
            self.telegram_bridge.start()

        self.webhook_server = WebhookServer(config=self.config)
        if self.webhook_server.enabled:
            self.webhook_server.start()

    def _init_updater(self):
        """Initialize auto-update checker."""
        self.updater = AppUpdater(config=self.config)
        self.updater.enabled = False # FORCE DISABLED FOR LOCAL DEV
        self._update_timer = None

        if not self.updater.enabled:
            return

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._run_update_check)
        interval_ms = max(1, self.updater.check_interval_hours) * 60 * 60 * 1000
        self._update_timer.start(interval_ms)
        QTimer.singleShot(2000, self._run_update_check)

    def _run_update_check(self):
        info = self.updater.check_for_updates()
        if not info:
            return
        path = self.updater.download_pending_update()
        if path:
            self.bubble_system.queue_message(
                f"Update {info['version']} ready. Contact: {self.updater.support_email}", "ambient"
            )

    def _init_brain(self):
        """Create the behavioral AI (used for future animated overlays)."""
        self.bubble_system = BubbleSystem(config=self.config)
        self.brain = BehavioralReactor(config=self.config)
        self.brain.set_bounds(*self.total_bounds)

        self.sanctuary = SanctuaryEngine(config=self.config)
        self.brain.set_sanctuary(self.sanctuary)
        self.brain.set_bubble_system(self.bubble_system)

    def _init_modules(self):
        """Initialize communication modules."""
        module_cfg = self.config.get("modules") or {}

        self.health_module = HealthModule(config=self.config, llm_brain=self.llm_brain)
        self.health_module.enabled = module_cfg.get("health", True)

        self.love_notes_module = LoveNotesModule(config=self.config)
        self.love_notes_module.enabled = module_cfg.get("love_notes", True)
        self.love_notes_module.set_telegram_bridge(self.telegram_bridge)
        self.love_notes_module.set_webhook_server(self.webhook_server)

        self.schedule_module = ScheduleModule(config=self.config)
        self.schedule_module.enabled = module_cfg.get("schedule", True)

        self.news_module = NewsModule(config=self.config, llm_brain=self.llm_brain)
        self.news_module.enabled = module_cfg.get("news", False)

        self.brain.add_module(self.health_module)
        self.brain.add_module(self.love_notes_module)
        self.brain.add_module(self.schedule_module)
        self.brain.add_module(self.news_module)

    def _init_overlay_manager(self):
        """Initialize the HTML overlay system."""
        self.overlay_manager = OverlayManager(config=self.config)
        if self.overlay_manager.available:
            # Restore previously active overlays
            self.overlay_manager.restore_state()
            logger.info("Overlay Manager ready — HTML overlays available")
            
            # Setup screensaver
            self._init_screensaver()
        else:
            logger.warning("Overlay Manager: QWebEngine not installed — HTML overlays disabled")

    def _init_screensaver(self):
        # 30 minutes (1800 seconds) inactivity timeout
        self.inactivity_tracker = InactivityTracker(timeout_seconds=1800, parent=None)
        self.inactivity_tracker.screensaver_triggered.connect(self._on_screensaver_triggered)
        self.inactivity_tracker.screensaver_dismissed.connect(self._on_screensaver_dismissed)
        logger.info("Screensaver inactive tracking started (30m timeout)")

    def _on_screensaver_triggered(self):
        logger.info("Screensaver triggered by inactivity")
        self.overlay_manager.open_overlay("fireflies")

    def _on_screensaver_dismissed(self):
        logger.info("Screensaver dismissed by user activity")
        self.overlay_manager.close_overlay("fireflies")

    def _init_tray(self):
        """Create system tray icon with settings menu."""
        self.tray = SystemTray(config=self.config, overlay_manager=self.overlay_manager)
        self.tray.signals.sanctuary_toggled.connect(self._on_sanctuary_toggled)
        self.tray.signals.sanctuary_add_monitor.connect(self._on_sanctuary_add_monitor)
        self.tray.signals.sanctuary_clear.connect(self._on_sanctuary_clear)
        self.tray.signals.module_toggled.connect(self._on_module_toggled)
        self.tray.signals.toggle_visibility.connect(self._on_toggle_visibility)
        self.tray.signals.quit_app.connect(self._on_quit)
        self.tray.signals.love_notes_path_set.connect(self._on_love_notes_path)
        self.tray.signals.telegram_token_set.connect(self._on_telegram_token)
        self.tray.signals.webhook_toggled.connect(self._on_webhook_toggled)
        self.tray.signals.llm_key_set.connect(self._on_llm_key_set)
        self.tray.signals.overlay_toggled.connect(self._on_overlay_toggled)
        self.tray.signals.fish_settings_changed.connect(self._on_fish_settings_changed)
        self.tray.signals.debug_canvas_extents.connect(self._on_debug_canvas_extents)
        self.tray.show()

    def _init_hotkeys(self):
        """Set up global hotkeys."""
        self._hotkey_listener = None
        try:
            from pynput import keyboard

            def on_visibility():
                QTimer.singleShot(0, self._on_toggle_visibility)

            def on_sanctuary():
                QTimer.singleShot(0, self._on_sanctuary_toggled)

            def on_interactivity():
                QTimer.singleShot(0, self._on_toggle_interactivity)

            def on_feed():
                QTimer.singleShot(0, self._on_feed_hotkey)

            def format_hotkey(hotkey_str):
                # pynput expects '<ctrl>+<alt>+h' not '<ctrl>+<alt>+<h>'
                parts = hotkey_str.split('+')
                formatted = []
                for p in parts:
                    if p in ('ctrl', 'alt', 'shift', 'cmd'):
                        formatted.append(f"<{p}>")
                    else:
                        formatted.append(p)
                return "+".join(formatted)

            hotkey_vis = format_hotkey(self.config.get('hotkeys', 'toggle_visibility'))
            hotkey_sanc = format_hotkey(self.config.get('hotkeys', 'toggle_sanctuary'))
            raw_int = self.config.get('hotkeys', 'toggle_interactivity')
            if not raw_int:
                raw_int = 'ctrl+alt+i'
            hotkey_int = format_hotkey(raw_int)
            hotkey_feed = format_hotkey(self.config.get('hotkeys', 'feed_fish') or 'ctrl+alt+f')

            hotkeys = {
                hotkey_vis: on_visibility,
                hotkey_sanc: on_sanctuary,
                hotkey_int: on_interactivity,
                hotkey_feed: on_feed,
            }

            self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
            logger.info("Global hotkeys registered (Ctrl+Alt+H=Toggle Overlays, S=Sanctuary, I=Interact)")
        except ImportError:
            logger.warning("pynput not available — global hotkeys disabled")
        except Exception as e:
            logger.warning(f"Hotkey setup failed: {e}")

    def _init_main_loop(self):
        """Set up the update loop for brain/modules."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)  # 1 second tick for modules (overlays render themselves)

    def _tick(self):
        """Main loop: update brain and modules."""
        self.brain.update()

    def _init_blue_vision_bridge(self):
        """Connect Blue Vision for screen context awareness."""
        import os
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        groq_key = os.environ.get('GROQ_API_KEY', '')
        scan_interval = max(60, int(self.config.get("vision", "scan_interval") or 300))

        try:
            from modules.blue_vision_bridge import BlueVisionBridge
            self.vision_bridge = BlueVisionBridge(api_key=groq_key, scan_interval=scan_interval)

            if self.vision_bridge.available:
                self.vision_bridge.start()
                self._vision_bridge_timer = QTimer()
                self._vision_bridge_timer.timeout.connect(self._apply_vision_context)
                self._vision_bridge_timer.start(10000)
                logger.info("Blue Vision Bridge active")
            else:
                self._vision_bridge_timer = None
        except ImportError:
            self.vision_bridge = None
            self._vision_bridge_timer = None
            logger.info("Blue Vision Bridge: not available")

    def _apply_vision_context(self):
        """Apply Blue Vision screen context to brain."""
        if not self.vision_bridge or not self.vision_bridge.available:
            return
        self.brain.set_screen_context(self.vision_bridge.context)
        self.vision_bridge.apply_to_brain(self.brain, self.bubble_system)

    def _update_tray_status(self):
        """Update integration status in tray menu."""
        parts = []
        if self.llm_brain.is_available:
            parts.append(f"LLM: {self.llm_brain.provider}")
        if self.telegram_bridge.enabled:
            parts.append("Telegram: ON")
        if self.webhook_server.enabled:
            parts.append(f"Webhook: :{self.webhook_server.port}")

        active_overlays = len(self.overlay_manager.get_active_ids())
        if active_overlays:
            parts.append(f"Overlays: {active_overlays} active")

        if not parts:
            parts.append("Ready — open an overlay to get started")
        self.tray.update_status(" | ".join(parts))

    # --- Signal handlers ---

    def _on_overlay_toggled(self, overlay_id):
        """Handle overlay toggle from tray menu."""
        was_active = self.overlay_manager.is_active(overlay_id)
        result = self.overlay_manager.toggle_overlay(overlay_id)

        # Update tray checkmarks
        self.tray.update_overlay_state(overlay_id, result)
        self._update_tray_status()

        # Get overlay name
        registry = {ov["id"]: ov for ov in self.overlay_manager.get_registry()}
        name = registry.get(overlay_id, {}).get("name", overlay_id)

        if result:
            self.bubble_system.queue_message(f"{name} overlay activated", "ambient")
        else:
            self.bubble_system.queue_message(f"{name} overlay closed", "ambient")

    def _on_fish_settings_changed(self):
        """Handle fish settings changes from the tray menu and reload overlays."""
        logger.info("Fish settings changed. Reloading active fish overlays...")
        for overlay_id in ["neon-tetra", "glass-fish"]:
            if self.overlay_manager.is_active(overlay_id):
                self.overlay_manager.close_overlay(overlay_id, save_state=False)
                self.overlay_manager.open_overlay(overlay_id)

    def _on_feed_hotkey(self):
        """Handle Ctrl+Alt+F to activate interactive spoon feeding mode."""
        logger.info("Feeding hotkey triggered.")
        if self.overlay_manager:
            self.overlay_manager.start_feeding_mode()
            self.bubble_system.queue_message("Feeding mode active! Click to drop food.", "ambient")

    def _on_toggle_visibility(self):
        """Toggle visibility of all overlays."""
        self.overlay_manager.toggle_all_visibility()

    def _on_toggle_interactivity(self):
        """Toggle interactivity for interactive overlays."""
        new_state = self.overlay_manager.toggle_interactivity()
        if new_state:
            self.bubble_system.queue_message("Interaction Mode ON", "ambient")
        else:
            self.bubble_system.queue_message("Interaction Mode OFF", "ambient")

    def _on_sanctuary_toggled(self):
        enabled = self.sanctuary.toggle()
        self.tray.update_sanctuary_toggle(enabled)
        self.config.set("sanctuary", "enabled", enabled)

    def _on_sanctuary_add_monitor(self, monitor_index):
        screens = QGuiApplication.screens()
        if 0 <= monitor_index < len(screens):
            geo = screens[monitor_index].geometry()
            self.sanctuary.add_monitor_zone(geo, f"Monitor {monitor_index + 1}")
            self.config.set("sanctuary", "zones", self.sanctuary.get_zones_as_dicts())
            if not self.sanctuary.enabled:
                self.sanctuary.enabled = True
                self.tray.update_sanctuary_toggle(True)
                self.config.set("sanctuary", "enabled", True)

    def _on_sanctuary_clear(self):
        self.sanctuary.clear_zones()
        self.config.set("sanctuary", "zones", [])

    def _on_module_toggled(self, module_key, enabled):
        module_map = {
            "health": self.health_module,
            "love_notes": self.love_notes_module,
            "schedule": self.schedule_module,
            "news": self.news_module,
        }
        if module_key in module_map:
            module_map[module_key].enabled = enabled
            self.config.set("modules", module_key, enabled)
            logger.info(f"Module '{module_key}' {'enabled' if enabled else 'disabled'}")

    def _on_love_notes_path(self, path):
        self.love_notes_module.set_source_path(path)
        self.config.set("love_notes", "source_path", path)

    def _on_telegram_token(self, token):
        self.config.set("telegram", "bot_token", token)
        self.telegram_bridge.token = token
        self.telegram_bridge.enabled = True
        self.telegram_bridge.start()
        self._update_tray_status()
        self.bubble_system.queue_message("Telegram connected!", "love")
        logger.info("Telegram bot token configured and bridge started.")

    def _on_webhook_toggled(self, enabled):
        self.config.set("webhook", "enabled", enabled)
        if enabled:
            self.webhook_server.enabled = True
            if self.webhook_server.start():
                self.bubble_system.queue_message(
                    f"Webhook listening on port {self.webhook_server.port}", "ambient"
                )
        else:
            self.webhook_server.stop()
            self.webhook_server.enabled = False
        self._update_tray_status()

    def _on_llm_key_set(self, provider, key):
        if provider == "anthropic":
            self.config.set("llm", "anthropic_api_key", key)
            self.config.set("llm", "provider", "anthropic")
        elif provider == "openai":
            self.config.set("llm", "openai_api_key", key)
            self.config.set("llm", "provider", "openai")

        self.llm_brain = LLMBrain(config=self.config)
        self.health_module.set_llm_brain(self.llm_brain)
        self.news_module.set_llm_brain(self.llm_brain)

        if self.llm_brain.is_available:
            self.bubble_system.queue_message(
                f"LLM Brain active! ({self.llm_brain.provider})", "ambient"
            )
        self._update_tray_status()
        logger.info(f"LLM key set for {provider}, brain re-initialized.")

    def _on_quit(self):
        logger.info("Ohverlay V4.0 shutting down...")
        self.timer.stop()
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        if hasattr(self, 'vision_bridge') and self.vision_bridge:
            self.vision_bridge.stop()
        if self._vision_bridge_timer:
            self._vision_bridge_timer.stop()
        self.overlay_manager.close_all()
        self.telegram_bridge.stop()
        self.webhook_server.stop()
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
    logger.info("Starting OHVERLAY...")
    app = OhverlayApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
