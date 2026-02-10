"""
ZenFish Overlay - Main entry point.
A transparent desktop companion: a lifelike Betta fish that swims natively
across your 2-3 monitors with no aquarium background. The monitors ARE the tank.

Features:
- LLM-powered health reminders and news curation (Claude/OpenAI)
- Real-time love notes via Telegram, WhatsApp/Messenger webhooks, or JSON file
- Sanctuary zones (invisible boundaries) for deep work
- Bubble communication system with category-based messages
"""

import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication

from engine.brain import BehavioralReactor
from engine.aquarium import MonitorManager, AquariumSector
from engine.sanctuary import SanctuaryEngine
from engine.school import FishSchool
from engine.llm_brain import LLMBrain
from ui.skin import FishSkin
from ui.tetra_skin import NeonTetraSkin
from ui.discus_skin import DiscusSkin
from ui.bubbles import BubbleSystem
from ui.tray import SystemTray
from config.settings import Settings
from modules.health import HealthModule
from modules.love_notes import LoveNotesModule
from modules.schedule import ScheduleModule
from modules.news import NewsModule
from modules.telegram_bridge import TelegramBridge
from modules.webhook_server import WebhookServer
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

        # Initialize subsystems (order matters)
        self._init_monitors()
        self._init_rendering()
        self._init_llm_brain()
        self._init_messaging()
        self._init_brain()
        self._init_modules()
        self._init_tray()
        self._init_hotkeys()
        self._init_sectors()
        self._init_main_loop()

        # Update tray status
        self._update_tray_status()

        logger.info("ZenFish Overlay fully initialized. Your betta is swimming!")

    def _init_monitors(self):
        """Detect monitors - they form the fish's entire world."""
        self.monitor_manager = MonitorManager()
        self.total_bounds = self.monitor_manager.get_total_bounds_tuple()

    def _init_rendering(self):
        """Create the fish skin renderer and bubble system."""
        self.skin = FishSkin(config=self.config)
        self.bubble_system = BubbleSystem(config=self.config)

        # School mode state (None = solo betta mode)
        self.school = None
        self.school_skins = []
        self.school_mode = False

    def _init_llm_brain(self):
        """Initialize the LLM Brain for intelligent orchestration."""
        self.llm_brain = LLMBrain(config=self.config)
        if self.llm_brain.is_available:
            logger.info(f"LLM Brain active: {self.llm_brain.provider} ({self.llm_brain.model})")
        else:
            logger.info("LLM Brain: no API key configured - using static fallback messages")

    def _init_messaging(self):
        """Initialize Telegram bridge and webhook server."""
        # Telegram
        self.telegram_bridge = TelegramBridge(config=self.config)
        if self.telegram_bridge.enabled:
            self.telegram_bridge.start()

        # Webhook server for WhatsApp/Messenger
        self.webhook_server = WebhookServer(config=self.config)
        if self.webhook_server.enabled:
            self.webhook_server.start()

    def _init_brain(self):
        """Create the behavioral AI and connect subsystems."""
        self.brain = BehavioralReactor(config=self.config)
        self.brain.set_bounds(*self.total_bounds)

        # Sanctuary engine (invisible boundaries)
        self.sanctuary = SanctuaryEngine(config=self.config)
        self.brain.set_sanctuary(self.sanctuary)

        # Bubble system for communication
        self.brain.set_bubble_system(self.bubble_system)

        # Restore persisted speed setting
        saved_speed = self.config.get("fish", "speed") if self.config else None
        if saved_speed:
            self._on_speed_changed(saved_speed)

    def _init_modules(self):
        """Initialize and register communication modules with LLM brain."""
        module_cfg = self.config.get("modules") or {}

        # Health module (LLM-enhanced)
        self.health_module = HealthModule(config=self.config, llm_brain=self.llm_brain)
        self.health_module.enabled = module_cfg.get("health", True)

        # Love notes (multi-source: file + telegram + webhook)
        self.love_notes_module = LoveNotesModule(config=self.config)
        self.love_notes_module.enabled = module_cfg.get("love_notes", True)
        self.love_notes_module.set_telegram_bridge(self.telegram_bridge)
        self.love_notes_module.set_webhook_server(self.webhook_server)

        # Schedule
        self.schedule_module = ScheduleModule(config=self.config)
        self.schedule_module.enabled = module_cfg.get("schedule", True)

        # News (LLM-enhanced)
        self.news_module = NewsModule(config=self.config, llm_brain=self.llm_brain)
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
        self.tray.signals.speed_changed.connect(self._on_speed_changed)
        self.tray.signals.telegram_token_set.connect(self._on_telegram_token)
        self.tray.signals.webhook_toggled.connect(self._on_webhook_toggled)
        self.tray.signals.llm_key_set.connect(self._on_llm_key_set)
        self.tray.signals.species_changed.connect(self._on_species_changed)
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
        if self.school_mode and self.school:
            # School mode: update all fish via Boids engine
            self.school.update()
            school_states = self.school.get_all_states()
            for sector in self.sectors:
                sector.update_school_states(school_states)
        else:
            # Solo betta mode
            self.brain.update()
            fish_state = self.brain.get_state()
            for sector in self.sectors:
                sector.update_fish_state(fish_state)

    def _update_tray_status(self):
        """Update integration status in tray menu."""
        parts = []
        if self.llm_brain.is_available:
            parts.append(f"LLM: {self.llm_brain.provider}")
        if self.telegram_bridge.enabled:
            parts.append("Telegram: ON")
        if self.webhook_server.enabled:
            parts.append(f"Webhook: :{self.webhook_server.port}")
        if not parts:
            parts.append("No integrations active")
        self.tray.update_status(" | ".join(parts))

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

    def _on_speed_changed(self, speed_key):
        """Adjust fish swimming speed."""
        speed_map = {
            "super_slow": {"max": 40, "cruise": 12, "idle": 5, "dart": 80, "label": "Super Slow"},
            "slow": {"max": 90, "cruise": 30, "idle": 10, "dart": 150, "label": "Slow"},
            "normal": {"max": 180, "cruise": 55, "idle": 20, "dart": 350, "label": "Normal"},
            "fast": {"max": 300, "cruise": 100, "idle": 35, "dart": 500, "label": "Fast"},
        }
        preset = speed_map.get(speed_key, speed_map["normal"])
        self.brain._max_speed = preset["max"]
        self.brain._cruise_speed = preset["cruise"]
        self.brain._idle_speed = preset["idle"]
        self.brain._dart_speed = preset["dart"]
        self.config.set("fish", "speed", speed_key)
        logger.info(f"Swimming speed set to: {preset['label']}")

    def _on_species_changed(self, species, count):
        """Switch between solo betta and school mode with different species."""
        if species == "betta" and count <= 1:
            # Return to solo betta mode
            self.school_mode = False
            self.school = None
            self.school_skins = []
            for sector in self.sectors:
                sector.set_school_skins([])
            logger.info("Switched to solo Betta mode.")
            self.bubble_system.queue_message("Solo betta mode.", "ambient")
            return

        # Create school with appropriate skins
        count = max(1, min(12, count))
        self.school = FishSchool(self.total_bounds, species=species, count=count)
        self.school.set_sanctuary(self.sanctuary)

        # Create one skin per fish with unique seeds for variation
        morph_list = list(DiscusSkin.MORPHS.keys())
        self.school_skins = []
        for i in range(count):
            if species == "neon_tetra":
                skin = NeonTetraSkin(seed=42 + i * 17)
            elif species == "discus":
                morph = morph_list[i % len(morph_list)]
                skin = DiscusSkin(seed=42 + i * 17, morph=morph)
            else:
                skin = NeonTetraSkin(seed=42 + i * 17)
            self.school_skins.append(skin)

        # Push skins to all sectors
        for sector in self.sectors:
            sector.set_school_skins(self.school_skins)

        self.school_mode = True
        self.config.set("fish", "species", species)
        self.config.set("fish", "school_count", count)

        label = species.replace("_", " ").title()
        logger.info(f"School mode: {count} {label}")
        self.bubble_system.queue_message(f"{count} {label} swimming!", "ambient")

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

    def _on_telegram_token(self, token):
        """Handle Telegram bot token configuration."""
        self.config.set("telegram", "bot_token", token)
        self.telegram_bridge.token = token
        self.telegram_bridge.enabled = True
        self.telegram_bridge.start()
        self._update_tray_status()
        self.bubble_system.queue_message("Telegram connected! Send me love notes.", "love")
        logger.info("Telegram bot token configured and bridge started.")

    def _on_webhook_toggled(self, enabled):
        """Toggle the webhook server on/off."""
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
        """Handle LLM API key configuration."""
        if provider == "anthropic":
            self.config.set("llm", "anthropic_api_key", key)
            self.config.set("llm", "provider", "anthropic")
        elif provider == "openai":
            self.config.set("llm", "openai_api_key", key)
            self.config.set("llm", "provider", "openai")

        # Re-initialize the LLM brain with new key
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
        logger.info("ZenFish shutting down...")
        self.timer.stop()
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        self.telegram_bridge.stop()
        self.webhook_server.stop()
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
