"""
ZenFish Overlay - Main entry point.
A transparent desktop companion: a lifelike Betta fish that swims natively
across your 2-3 monitors with no aquarium background. The monitors ARE the tank.
"""

import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication

from engine.brain import BehavioralReactor
from engine.aquarium import MonitorManager, AquariumSector
from engine.sanctuary import SanctuaryEngine
from ui.skin import FishSkin
from ui.bubbles import BubbleSystem
from ui.tray import SystemTray
from config.settings import Settings
from modules.health import HealthModule
from modules.love_notes import LoveNotesModule
from modules.schedule import ScheduleModule
from modules.news import NewsModule
from utils.logger import logger


class ZenFishApp:
    """Main application controller wiring all systems together."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ZenFish Overlay")
        self.app.setQuitOnLastWindowClosed(False)

        # Allow Ctrl+C to exit from terminal
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Load configuration
        self.config = Settings()

        # Initialize subsystems
        self._init_monitors()
        self._init_rendering()
        self._init_brain()
        self._init_modules()
        self._init_tray()
        self._init_hotkeys()
        self._init_sectors()
        self._init_main_loop()

        logger.info("ZenFish Overlay fully initialized. Your betta is swimming!")

    def _init_monitors(self):
        """Detect monitors - they form the fish's entire world."""
        self.monitor_manager = MonitorManager()
        self.total_bounds = self.monitor_manager.get_total_bounds_tuple()

    def _init_rendering(self):
        """Create the fish skin renderer and bubble system."""
        self.skin = FishSkin(config=self.config)
        self.bubble_system = BubbleSystem(config=self.config)

    def _init_brain(self):
        """Create the behavioral AI and connect subsystems."""
        self.brain = BehavioralReactor()
        self.brain.set_bounds(*self.total_bounds)

        # Sanctuary engine (invisible boundaries)
        self.sanctuary = SanctuaryEngine(config=self.config)
        self.brain.set_sanctuary(self.sanctuary)

        # Bubble system for communication
        self.brain.set_bubble_system(self.bubble_system)

    def _init_modules(self):
        """Initialize and register communication modules."""
        module_cfg = self.config.get("modules") or {}

        self.health_module = HealthModule(config=self.config)
        self.health_module.enabled = module_cfg.get("health", True)

        self.love_notes_module = LoveNotesModule(config=self.config)
        self.love_notes_module.enabled = module_cfg.get("love_notes", True)

        self.schedule_module = ScheduleModule(config=self.config)
        self.schedule_module.enabled = module_cfg.get("schedule", True)

        self.news_module = NewsModule(config=self.config)
        self.news_module.enabled = module_cfg.get("news", False)

        self.brain.add_module(self.health_module)
        self.brain.add_module(self.love_notes_module)
        self.brain.add_module(self.schedule_module)
        self.brain.add_module(self.news_module)

    def _init_tray(self):
        """Create system tray icon with settings menu."""
        self.tray = SystemTray(config=self.config)
        self.tray.signals.color_changed.connect(self._on_color_changed)
        self.tray.signals.sanctuary_toggled.connect(self._on_sanctuary_toggled)
        self.tray.signals.sanctuary_add_monitor.connect(self._on_sanctuary_add_monitor)
        self.tray.signals.sanctuary_clear.connect(self._on_sanctuary_clear)
        self.tray.signals.module_toggled.connect(self._on_module_toggled)
        self.tray.signals.feed_fish.connect(self._on_feed_fish)
        self.tray.signals.toggle_visibility.connect(self._on_toggle_visibility)
        self.tray.signals.quit_app.connect(self._on_quit)
        self.tray.signals.love_notes_path_set.connect(self._on_love_notes_path)
        self.tray.signals.size_changed.connect(self._on_size_changed)
        self.tray.show()

    def _init_hotkeys(self):
        """Set up global hotkeys (best-effort, non-blocking)."""
        self._hotkey_listener = None
        try:
            from pynput import keyboard

            def on_feed():
                QTimer.singleShot(0, self._on_feed_fish)

            def on_sanctuary():
                QTimer.singleShot(0, self._on_sanctuary_toggled)

            def on_visibility():
                QTimer.singleShot(0, self._on_toggle_visibility)

            hotkeys = {
                '<ctrl>+<alt>+f': on_feed,
                '<ctrl>+<alt>+s': on_sanctuary,
                '<ctrl>+<alt>+h': on_visibility,
            }

            self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
            logger.info("Global hotkeys registered (Ctrl+Alt+F/S/H).")
        except ImportError:
            logger.warning("pynput not available - global hotkeys disabled. Install with: pip install pynput")
        except Exception as e:
            logger.warning(f"Hotkey setup failed: {e}")

    def _init_sectors(self):
        """Create transparent overlay windows for each monitor."""
        self.sectors = []
        for i, screen in enumerate(self.monitor_manager.screens):
            sector = AquariumSector(
                screen.geometry(), i,
                skin=self.skin,
                bubble_system=self.bubble_system
            )
            sector.show()
            self.sectors.append(sector)

    def _init_main_loop(self):
        """Set up the 30 FPS update loop."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)  # ~30 FPS

    def _tick(self):
        """Main loop: update brain AI, then push state to all screen sectors."""
        self.brain.update()
        fish_state = self.brain.get_state()
        for sector in self.sectors:
            sector.update_fish_state(fish_state)

    # --- Signal handlers ---

    def _on_color_changed(self, primary, secondary, accent):
        self.skin.set_colors(primary, secondary, accent)
        self.config.set("fish", "primary_color", list(primary))
        self.config.set("fish", "secondary_color", list(secondary))
        self.config.set("fish", "accent_color", list(accent))
        logger.info(f"Fish color changed to: {primary}")

    def _on_size_changed(self, scale):
        self.skin.size_scale = scale
        self.config.set("fish", "size_scale", scale)
        logger.info(f"Fish size set to: {scale}x")

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

    def _on_feed_fish(self):
        self.brain.feed()
        self.bubble_system.queue_message("Yum! Thank you!", "ambient")

    def _on_toggle_visibility(self):
        for sector in self.sectors:
            sector.set_visible(not sector.visible)

    def _on_love_notes_path(self, path):
        self.love_notes_module.set_source_path(path)
        self.config.set("love_notes", "source_path", path)

    def _on_quit(self):
        logger.info("ZenFish shutting down...")
        self.timer.stop()
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        self.config.save()
        self.app.quit()

    def run(self):
        """Start the application event loop."""
        return self.app.exec()


def main():
    logger.info("Starting ZenFish Overlay...")
    app = ZenFishApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
