"""
OHVERLAY V4.0 - Assistant's Division
A transparent desktop companion: Deep sea creatures and non-biological objects
swim across your 2-3 monitors. The monitors ARE the world.

Division Split:
- Assistant: Jellyfish, Geometric, Energy Orbs, Holographic, Airplane, Train, Submarine
- Lumex: Betta, Tetra, Discus, Plants (separate package)

Features:
- LLM-powered health reminders and news curation (Claude/OpenAI)
- Real-time love notes via Telegram, WhatsApp/Messenger webhooks, or JSON file
- Sanctuary zones (invisible boundaries) for deep work
- Bubble communication system with category-based messages
"""

import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QBuffer, QByteArray
from PySide6.QtGui import QGuiApplication, QCursor

from engine.brain import BehavioralReactor
from engine.aquarium import MonitorManager, AquariumSector
from engine.sanctuary import SanctuaryEngine
from engine.llm_brain import LLMBrain
from ui.jellyfish_skin import BioluminescentJellyfishSkin
from ui.jellyfish_iridescent_skin import IridescentJellyfishSkin
from ui.bubbles import BubbleSystem

# MOVED TO LUMEX PACKAGE (Betta, Tetra, Discus, Plants):
# from engine.school import FishSchool
# from ui.skin import FishSkin
# from ui.skin_realistic import RealisticBettaSkin
# from ui.tetra_skin import NeonTetraSkin

# Non-biological objects (Assistant's division)
from ui.geometric_skin import GeometricShapes
from ui.energy_orb_skin import EnergyOrbSystem
from ui.holographic_skin import HolographicInterface
from ui.airplane_skin import Airplane
from ui.train_skin import VintageSteamTrain
from ui.submarine_skin import RealisticSubmarine
from ui.balloon_skin import HotAirBalloon

# LUMEX owns: Betta fish, Discus, Neon Tetra, Plants
# ASSISTANT owns: Jellyfish, Geometric, Energy Orbs, Holographic, Airplane, Train, Submarine
from ui.tray import SystemTray
from config.settings import Settings
from modules.health import HealthModule
from modules.love_notes import LoveNotesModule
from modules.schedule import ScheduleModule
from modules.news import NewsModule
from modules.telegram_bridge import TelegramBridge
from modules.webhook_server import WebhookServer
from modules.updater import AppUpdater
from utils.logger import logger


class OhverlayApp:
    """Main application controller wiring all systems together."""

    def __init__(self):
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
        self._init_rendering()
        self._init_llm_brain()
        self._init_messaging()
        self._init_updater()
        self._init_brain()
        self._init_modules()
        self._init_tray()
        self._init_hotkeys()
        self._init_sectors()
        self._restore_fish_mode()
        self._init_main_loop()
        self._init_vision_foraging()

        # Update tray status
        self._update_tray_status()

        logger.info("OHVERLAY V4.0 fully initialized! Assistant's Division Active: Deep Sea + Non-Bio creatures ready!")

    def _init_monitors(self):
        """Detect monitors - they form the creature's entire world."""
        self.monitor_manager = MonitorManager()
        self.total_bounds = self.monitor_manager.get_total_bounds_tuple()

    def _init_rendering(self):
        """Create the creature renderer - Assistant's Division (Deep Sea + Non-Bio only)."""
        # Get creature type from config (default: jellyfish - Lumex owns Betta now)
        try:
            # Access creature_type directly from root config (not via get() which expects section)
            creature_type = self.config._config.get("creature_type", "jellyfish")
            if not creature_type or creature_type in ["betta", "discus", "neon_tetra"]:
                # Betta/Tetra/Discus moved to LUMEX - default to jellyfish
                creature_type = "jellyfish"
        except:
            creature_type = "jellyfish"
        self.creature_type = creature_type.lower()
        
        # Initialize non-biological object skins (Assistant's division)
        self.non_bio_skin = None
        
        if self.creature_type == "jellyfish":
            # Deep sea bioluminescent jellyfish
            self.skin = BioluminescentJellyfishSkin(config=self.config)
            logger.info("Using BIOLUMINESCENT JELLYFISH - Deep sea variant with glowing lights!")
        elif self.creature_type == "iridescent_jellyfish":
            # Deep sea rainbow iridescent jellyfish
            self.skin = IridescentJellyfishSkin(config=self.config)
            logger.info("Using IRIDESCENT JELLYFISH - Rainbow bioluminescent deep sea creature!")
        elif self.creature_type == "geometric":
            self.non_bio_skin = GeometricShapes(config=self.config)
            self.skin = None
            self.non_bio_skin.show()
            logger.info("Using GEOMETRIC SHAPES - Floating crystalline formations!")
        elif self.creature_type == "energy_orbs":
            self.non_bio_skin = EnergyOrbSystem(config=self.config)
            self.skin = None
            self.non_bio_skin.show()
            logger.info("Using ENERGY ORBS - Glowing orbs with light trails!")
        elif self.creature_type == "holographic":
            self.non_bio_skin = HolographicInterface(config=self.config)
            self.skin = None
            self.non_bio_skin.show()
            logger.info("Using HOLOGRAPHIC INTERFACE - Sci-fi data display!")
        elif self.creature_type == "airplane":
            self.non_bio_skin = Airplane(config=self.config)
            self.skin = None
            self.non_bio_skin.show()
            logger.info("Using AIRPLANE - Jet aircraft with contrails!")
        elif self.creature_type == "train":
            self.non_bio_skin = VintageSteamTrain(config=self.config)
            self.skin = None
            self.non_bio_skin.show()
            logger.info("Using TRAIN - Steam locomotive on desktop edges!")
        elif self.creature_type == "submarine":
            self.non_bio_skin = RealisticSubmarine(config=self.config)
            self.skin = None
            self.non_bio_skin.show()
            logger.info("Using SUBMARINE - Torpedo-firing underwater vessel!")
        elif self.creature_type == "balloon":
            self.non_bio_skin = HotAirBalloon(config=self.config)
            self.skin = None
            self.non_bio_skin.show()
            logger.info("Using HOT AIR BALLOON - Colorful floating adventure!")
        else:
            # Default to jellyfish
            self.creature_type = "jellyfish"
            self.skin = BioluminescentJellyfishSkin(config=self.config)
            logger.info("Using BIOLUMINESCENT JELLYFISH - Deep sea variant with glowing lights!")
        
        self.bubble_system = BubbleSystem(config=self.config)
        
        # School mode disabled - Lumex owns school/betta
        self.school = None
        self.school_skins = []
        self.school_mode = False
    
    def _get_system_ram_gb(self):
        """Get total system RAM in GB."""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            # Fallback: try reading from Windows WMI
            try:
                import subprocess
                result = subprocess.run(['wmic', 'computersystem', 'get', 'totalphysicalmemory'], 
                                      capture_output=True, text=True)
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip().isdigit()]
                if lines:
                    return int(lines[0]) / (1024**3)
            except:
                pass
            # Default to basic if can't detect
            return 16.0

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

    def _init_updater(self):
        """Initialize lightweight auto-update checker/downloader."""
        self.updater = AppUpdater(config=self.config)
        self._update_timer = None

        if not self.updater.enabled:
            return

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._run_update_check)
        interval_ms = max(1, self.updater.check_interval_hours) * 60 * 60 * 1000
        self._update_timer.start(interval_ms)

        # Run one startup check in background cadence.
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

            def on_creature_toggle():
                QTimer.singleShot(0, self._on_toggle_creature)

            hotkeys = {
                '<ctrl>+<alt>+f': on_feed,
                '<ctrl>+<alt>+s': on_sanctuary,
                '<ctrl>+<alt>+h': on_visibility,
                '<ctrl>+<alt>+j': on_creature_toggle,  # Toggle jellyfish/betta
            }

            self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
            logger.info("Global hotkeys registered (Ctrl+Alt+F=Feed/Flash, S=Sanctuary, H=Hide, J=Toggle Creature).")
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
                bubble_system=self.bubble_system,
                config=self.config
            )
            sector.show()
            self.sectors.append(sector)

    def _restore_fish_mode(self):
        """Restore persisted species/school mode after sectors exist."""
        species = str(self.config.get("fish", "species") or "betta").strip().lower()
        raw_count = self.config.get("fish", "school_count")
        try:
            count = int(raw_count) if raw_count is not None else 1
        except (TypeError, ValueError):
            count = 1

        if species == "betta" and count <= 1:
            return
        if species not in {"betta", "neon_tetra", "discus"}:
            species = "neon_tetra"
        self._on_species_changed(species, max(1, count))

    def _init_main_loop(self):
        """Set up the 30 FPS update loop."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)  # ~30 FPS

    def _tick(self):
        """Main loop: update creatures and render to screen sectors."""
        # Update non-biological widget-based objects (Assistant's division)
        # These are: geometric, energy_orbs, holographic, airplane, train, submarine
        # (Jellyfish use sector rendering like the original betta)
        if self.non_bio_skin:
            cursor = QCursor.pos()
            dt = 0.033  # ~30 FPS
            self.non_bio_skin.update_state(dt, cursor.x(), cursor.y())
            # Only return early for true non-bio widgets
            if self.creature_type in ["geometric", "energy_orbs", "holographic", "airplane", "train", "submarine", "balloon"]:
                return  # Skip jellyfish update for widget-based creatures
        
        # Deep sea creatures mode (jellyfish variants)
        # Uses brain for movement AI, renders via sectors
        self.brain.update()
        fish_state = self.brain.get_state()
        for sector in self.sectors:
            sector.update_fish_state(fish_state)
        
        # Check for submarine eye rest reminder
        if self.creature_type == "submarine" and self.non_bio_skin:
            if getattr(self.non_bio_skin, 'show_reminder', False):
                # Show eye rest bubble message once per reminder
                if not getattr(self, '_last_eye_rest_shown', False):
                    self.bubble_system.queue_message(
                        "🔔 20-20-20 EYE REST! Torpedo fired! Look 20 feet away for 20 seconds!", 
                        "health"
                    )
                    self._last_eye_rest_shown = True
            else:
                self._last_eye_rest_shown = False

    def _init_vision_foraging(self):
        """Optional OpenAI vision loop: hourly screenshot analysis for playful auto-feeding."""
        self.vision_timer = None
        if not self.llm_brain.can_use_vision_foraging:
            return

        interval_min = max(5, int(self.config.get("llm", "vision_interval_minutes") or 60))
        self.vision_timer = QTimer()
        self.vision_timer.timeout.connect(self._run_vision_foraging)
        self.vision_timer.start(interval_min * 60 * 1000)
        logger.info(f"Vision foraging enabled (every {interval_min} min).")

    def _run_vision_foraging(self):
        if not self.llm_brain.can_use_vision_foraging:
            return

        screen = QGuiApplication.primaryScreen()
        if not screen:
            return

        pixmap = screen.grabWindow(0)
        if pixmap.isNull():
            return

        image = pixmap.toImage()
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QBuffer.WriteOnly)
        image.save(buf, "PNG")
        png_bytes = bytes(ba)

        def _on_result(result):
            QTimer.singleShot(0, lambda: self._apply_vision_foraging_result(result))

        self.llm_brain.analyze_screen_foraging_async(png_bytes, callback=_on_result)

    def _apply_vision_foraging_result(self, result):
        action = (result.get("action") or "none").lower()
        msg = result.get("message") or ""
        targets = result.get("targets") or []

        if action == "feed":
            self._on_feed_fish()
            if msg:
                self.bubble_system.queue_message(msg, "ambient")
            elif targets:
                target_str = ", ".join(str(t) for t in targets[:3])
                self.bubble_system.queue_message(f"Exploring near: {target_str}", "ambient")
            else:
                self.bubble_system.queue_message("Exploring your screen!", "ambient")

    def _update_tray_status(self):
        """Update integration status in tray menu."""
        parts = []
        if self.llm_brain.is_available:
            parts.append(f"LLM: {self.llm_brain.provider}")
        if self.telegram_bridge.enabled:
            parts.append("Telegram: ON")
        if self.webhook_server.enabled:
            parts.append(f"Webhook: :{self.webhook_server.port}")
        if self.llm_brain.can_use_vision_foraging:
            parts.append("Vision: ON")
        if not parts:
            parts.append("No integrations active")
        self.tray.update_status(" | ".join(parts))

    # --- Signal handlers ---

    def _on_color_changed(self, primary, secondary, accent):
        self.skin.set_colors(primary, secondary, accent)
        self.config.set("fish", "primary_color", list(primary))
        self.config.set("fish", "secondary_color", list(secondary))
        self.config.set("fish", "accent_color", list(accent))
        logger.info(f"Creature colors updated")

    def _on_size_changed(self, scale):
        self.skin.size_scale = scale
        self.config.set("fish", "size_scale", scale)
        logger.info(f"Creature size set to: {scale}x")

    def _on_speed_changed(self, speed_key):
        """Adjust creature swimming speed."""
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
        logger.info(f"Movement speed set to: {preset['label']}")

    def _on_species_changed(self, species, count):
        """School mode disabled - moved to LUMEX division (Betta/Tetra/Discus/Plants)."""
        self.bubble_system.queue_message("School mode available in LUMEX version only. Use Ctrl+Alt+J to toggle creatures!", "ambient")
        logger.info("School mode requested but disabled - moved to LUMEX division")

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
        """Trigger creature special effect (Ctrl+Alt+F)"""
        if self.creature_type in ["jellyfish", "iridescent_jellyfish"]:
            # Trigger bioluminescent flash for jellyfish
            if hasattr(self.skin, 'trigger_flash'):
                self.skin.trigger_flash()
            self.bubble_system.queue_message("✨ Bioluminescent display triggered! Beautiful light show!", "ambient")
        elif self.creature_type == "submarine":
            # Fire torpedo for submarine
            if self.non_bio_skin and hasattr(self.non_bio_skin, 'fire_torpedo'):
                self.non_bio_skin.fire_torpedo()
            self.bubble_system.queue_message("🚢 Torpedo fired! Bubble burst detected!", "ambient")
        else:
            self.bubble_system.queue_message(f"✨ Special effect triggered on {self.creature_type}!", "ambient")

    def _on_toggle_visibility(self):
        for sector in self.sectors:
            sector.set_visible(not sector.visible)

    def _on_toggle_creature(self):
        """Toggle through Assistant's creatures: Jellyfish → Iridescent → Geometric → Energy Orbs → Holographic → Airplane → Train → Submarine → Jellyfish
        
        NOTE: Betta fish, Tetra, Discus, and Plants moved to LUMEX division.
        """
        
        # Define the creature cycle
        # Creature cycle (ASSISTANT'S DIVISION only - Lumex owns Betta/Plants)
        # Deep sea creatures + Non-biological objects
        creature_cycle = [
            "jellyfish",            # Deep sea
            "iridescent_jellyfish", # Deep sea rainbow
            "geometric",            # Non-bio
            "energy_orbs",          # Non-bio
            "holographic",          # Non-bio
            "airplane",             # Non-bio
            "train",                # Non-bio - Vintage steam
            "submarine",            # Non-bio - With eye rest reminder
            "balloon"               # Non-bio - Hot air balloon
        ]
        
        # Get next creature in cycle
        try:
            current_idx = creature_cycle.index(self.creature_type)
        except ValueError:
            current_idx = 0
        
        next_idx = (current_idx + 1) % len(creature_cycle)
        next_creature = creature_cycle[next_idx]
        
        # Hide previous non-bio skin if exists
        if self.non_bio_skin:
            self.non_bio_skin.hide()
            self.non_bio_skin = None
        
        # Initialize new creature (Assistant's division only - no Betta/Tetra/Discus/Plants)
        if next_creature == "jellyfish":
            self.creature_type = "jellyfish"
            self.skin = BioluminescentJellyfishSkin(config=self.config)
            for sector in self.sectors:
                sector.skin = self.skin
            self.bubble_system.queue_message("🎆 Switched to BIOLUMINESCENT JELLYFISH! Press Ctrl+Alt+F to trigger light show!", "ambient")
            logger.info("Switched to Jellyfish mode")
            
        elif next_creature == "iridescent_jellyfish":
            self.creature_type = "iridescent_jellyfish"
            self.skin = IridescentJellyfishSkin(config=self.config)
            for sector in self.sectors:
                sector.skin = self.skin
            self.bubble_system.queue_message("🌈 Switched to IRIDESCENT JELLYFISH! Rainbow deep sea bioluminescence!", "ambient")
            logger.info("Switched to Iridescent Jellyfish mode")
            
        elif next_creature == "geometric":
            self.creature_type = "geometric"
            self.skin = None
            self.non_bio_skin = GeometricShapes(config=self.config)
            for sector in self.sectors:
                sector.skin = None  # No fish skin in non-bio mode
            self.non_bio_skin.show()
            self.bubble_system.queue_message("🔷 Switched to GEOMETRIC SHAPES - Floating crystals!", "ambient")
            logger.info("Switched to Geometric Shapes mode")
            
        elif next_creature == "energy_orbs":
            self.creature_type = "energy_orbs"
            self.skin = None
            self.non_bio_skin = EnergyOrbSystem(config=self.config)
            for sector in self.sectors:
                sector.skin = None
            self.non_bio_skin.show()
            self.bubble_system.queue_message("⚡ Switched to ENERGY ORBS - Glowing light trails!", "ambient")
            logger.info("Switched to Energy Orbs mode")
            
        elif next_creature == "holographic":
            self.creature_type = "holographic"
            self.skin = None
            self.non_bio_skin = HolographicInterface(config=self.config)
            for sector in self.sectors:
                sector.skin = None
            self.non_bio_skin.show()
            self.bubble_system.queue_message("🔮 Switched to HOLOGRAPHIC INTERFACE - Sci-fi display!", "ambient")
            logger.info("Switched to Holographic mode")
            
        elif next_creature == "airplane":
            self.creature_type = "airplane"
            self.skin = None
            self.non_bio_skin = Airplane(config=self.config)
            for sector in self.sectors:
                sector.skin = None
            self.non_bio_skin.show()
            self.bubble_system.queue_message("✈️ Switched to AIRPLANE - Jet with contrails!", "ambient")
            logger.info("Switched to Airplane mode")
            
        elif next_creature == "train":
            self.creature_type = "train"
            self.skin = None
            self.non_bio_skin = VintageSteamTrain(config=self.config)
            for sector in self.sectors:
                sector.skin = None
            self.non_bio_skin.show()
            self.bubble_system.queue_message("🚂 Switched to TRAIN - Steam locomotive!", "ambient")
            logger.info("Switched to Train mode")
            
        elif next_creature == "submarine":
            self.creature_type = "submarine"
            self.skin = None
            self.non_bio_skin = RealisticSubmarine(config=self.config)
            for sector in self.sectors:
                sector.skin = None
            self.non_bio_skin.show()
            self.bubble_system.queue_message("🚢 Switched to SUBMARINE - Torpedo-firing vessel!", "ambient")
            logger.info("Switched to Submarine mode")
            
        elif next_creature == "balloon":
            self.creature_type = "balloon"
            self.skin = None
            self.non_bio_skin = HotAirBalloon(config=self.config)
            for sector in self.sectors:
                sector.skin = None
            self.non_bio_skin.show()
            self.bubble_system.queue_message("🎈 Switched to HOT AIR BALLOON - Floating in the clouds!", "ambient")
            logger.info("Switched to Hot Air Balloon mode")
        
        # Save preference
        self.config.set("creature_type", self.creature_type)

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

        if self.vision_timer:
            self.vision_timer.stop()
            self.vision_timer = None
        self._init_vision_foraging()
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
        if self.vision_timer:
            self.vision_timer.stop()
        self.telegram_bridge.stop()
        self.webhook_server.stop()
        self.config.save()
        self.app.quit()

    def run(self):
        """Start the application event loop."""
        return self.app.exec()


def main():
    logger.info("Starting OHVERLAY...")
    app = OhverlayApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
