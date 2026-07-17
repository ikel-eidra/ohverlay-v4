# Architecture

The minimal Ohverlay nature baseline uses a lightweight, fully offline architecture.

## Core Components
- **`main.py`**: The entry point. Initializes the PySide6 Qt application, configures the event loop, and starts the core services.
- **`ui/tray.py`**: Provides the system tray icon and context menu. This is the sole method of user interaction, allowing the user to toggle overlays on or off, adjust sizes, and quit the app.
- **`config/settings.py`**: Manages local JSON persistence. Reads from and writes to `~/.ohverlay/config.json`.
- **`modules/overlay_manager.py`**: The core rendering manager. It creates frameless, transparent `QWebEngineView` windows that span the entire virtual desktop.

## Objects
Objects are implemented purely as local HTML files that utilize Canvas or WebGL for rendering:
- `fireflies-overlay.html`
- `dragonflies-overlay.html`
- `dandelions-overlay.html`

These files are loaded into the transparent `QWebEngineView` by the `OverlayManager`. They run independently without requiring any local backend APIs, network resources, or external dependencies.

## Rendering Pipeline
1. `OverlayManager` calculates the total geometry of all connected monitors.
2. A single `QMainWindow` with `Qt.WA_TranslucentBackground`, `Qt.FramelessWindowHint`, and `Qt.WindowTransparentForInput` is created spanning this geometry.
3. A `QWebEngineView` renders the requested object HTML file.
4. The background of the `QWebEnginePage` is forced to transparent, leaving only the drawn canvas elements visible.

This produces a click-through overlay that floats gently above the user's workspace without blocking interaction.
