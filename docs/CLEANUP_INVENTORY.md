# Cleanup Inventory

Classification of all root-level directories and major files for the Canonical Minimal Ohverlay Nature Baseline.

| File / Directory | Classification | Justification |
| :--- | :--- | :--- |
| `fireflies-overlay.html` | **KEEP — Object** | Verified Fireflies implementation |
| `dragonflies-overlay.html` | **KEEP — Object** | Verified Dragonflies implementation |
| `dandelion-overlay.html` | **KEEP — Object** | Verified Dandelions implementation |
| `main.py` | **REWRITE** | Entry point for the runtime; must be stripped of AI/messaging/fish initializations |
| `ui/tray.py` | **REWRITE** | Required for user controls (show/hide/quit), but must be stripped of non-approved options |
| `config/settings.py` | **REWRITE** | Required for local persistence; must be stripped of AI/messaging/fish settings |
| `modules/overlay_manager.py` | **REWRITE** | Manages transparent window creation; must remove chatbox logic |
| `utils/logger.py` | **KEEP — Runtime** | Provides necessary local diagnostic logging |
| `engine/` | **DELETE** | Contains only fish behavior, AI, and schooling systems; not required by HTML objects |
| `plumberpass/` | **DELETE** | Learning tools are out of scope for the current baseline |
| `ovl/` | **DELETE** | OVL compiler and language are out of scope |
| `LUMEX_PACKAGE/` | **DELETE** | LUMEX is out of scope |
| `factory/` | **DELETE** | Factory client and generated overlays out of scope. (Note: Retained overlays moved to `overlays/` or root) |
| `website/` | **DELETE** | Website code unused by local runtime |
| `modules/blue_memory.py` | **DELETE** | AI Memory out of scope |
| `modules/blue_realtime.py` | **DELETE** | AI realtime integration out of scope |
| `modules/blue_vision.py` | **DELETE** | Screen vision out of scope |
| `modules/blue_vision_bridge.py`| **DELETE** | Screen vision bridge out of scope |
| `modules/factory_client.py` | **DELETE** | Factory backend out of scope |
| `modules/health.py` | **DELETE** | Health reminders out of scope |
| `modules/inactivity_tracker.py` | **DELETE** | Inactivity tracking out of scope |
| `modules/love_notes.py` | **DELETE** | Love notes out of scope |
| `modules/news.py` | **DELETE** | News/RSS out of scope |
| `modules/schedule.py` | **DELETE** | Scheduling out of scope |
| `modules/telegram_bridge.py` | **DELETE** | Telegram integration out of scope |
| `modules/updater.py` | **DELETE** | Updater prototypes out of scope for now |
| `modules/webhook_server.py` | **DELETE** | Webhook server out of scope |
| `tests/test_aquarium.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_brain.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_bubbles.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_llm_brain.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_perlin.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_sanctuary.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_school.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_skins.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_updater.py` | **DELETE** | Unrelated to approved objects |
| `tests/test_config.py` | **REWRITE** | Need to rewrite to test only the minimal settings |
| `tests/test_modules.py` | **REWRITE** | Rewrite for the minimal overlay manager |
| `build.py` | **REWRITE** | Simplify for canonical build |
| `installer.iss` | **REWRITE** | Simplify for canonical installation |
| `build_installer.bat` | **KEEP — Project** | Required wrapper script |
| `build_portable_zip.bat` | **KEEP — Project** | Required wrapper script |
| `build_windows.bat` | **DELETE** | Duplicate/obsolete build script |
| `build_ecosystem.py` | **DELETE** | Obsolete build script |
| `ohverlay.spec` | **REWRITE** | Update PyInstaller spec for minimal baseline |
| `requirements.txt` | **REWRITE** | Strip unused dependencies |
| `requirements-dev.txt` | **KEEP — Project** | Minimal dev dependencies |
| `README.md` | **REWRITE** | Needs focused rewrite around the three objects |
| `PRIVACY.md` | **REWRITE** | Adjust to state the actual minimal privacy surface |
| `docs/TECHNICAL_OFFICE.md` | **DELETE** | Postponed |
| `docs/OVERLAY_PACKAGE_FORMAT.md`| **DELETE** | Postponed |

## Traced Dependencies for Retained Source Files

### `main.py`
- **Imports:** `ui.tray.SystemTray`, `config.settings.Settings`, `modules.overlay_manager.OverlayManager`, `utils.logger.logger`
- **Needed by:** The end user to launch the application.
- **Responsibility:** Orchestrates PySide6 initialization and creates the tray.
- **Privacy Impact:** Local process only. No network, screen, or file activity beyond loading configs.
- **Why it can't be replaced:** Essential entry point for the Python/Qt architecture.

### `ui/tray.py`
- **Imports:** `PySide6.QtWidgets`, `config.settings.Settings`, `modules.overlay_manager.OverlayManager`
- **Needed by:** End user to control overlays.
- **Responsibility:** Provides the system tray icon, context menu, and signals to toggle overlays.
- **Privacy Impact:** None.
- **Why it can't be replaced:** Required for background desktop applications on Windows.

### `config/settings.py`
- **Imports:** `json`, `os`
- **Needed by:** `main.py`, `ui/tray.py`, `modules.overlay_manager.OverlayManager`
- **Responsibility:** Reads/writes local user preferences (which overlays are enabled).
- **Privacy Impact:** Reads and writes `~/.ohverlay/config.json`.
- **Why it can't be replaced:** Requires local persistence so users don't have to re-enable fireflies every boot.

### `modules/overlay_manager.py`
- **Imports:** `PySide6.QtWebEngineWidgets`, `config.settings.Settings`
- **Needed by:** `main.py`, `ui/tray.py`
- **Responsibility:** Creates frameless, transparent `QWebEngineView` windows and loads the HTML objects. Handles multi-monitor geometry (via Qt APIs).
- **Privacy Impact:** Reads screen geometry to position overlays. No network access.
- **Why it can't be replaced:** QtWebEngine is the proven local renderer for HTML5 transparent overlays in Python.

### `utils/logger.py`
- **Imports:** `logging`, `logging.handlers`, `os`
- **Needed by:** Almost all files.
- **Responsibility:** Writes diagnostic logs to `~/.ohverlay/ohverlay.log`.
- **Privacy Impact:** Creates local file. No sensitive data logged in the minimal baseline.
- **Why it can't be replaced:** Diagnostic output is essential for debugging builds.
