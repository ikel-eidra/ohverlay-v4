# Ohverlay

Ohverlay is a minimal, lightweight desktop overlay runtime designed to render calm, animated nature objects across your entire screen workspace. It operates silently and transparently over your desktop without capturing your screen, reading your data, or demanding system resources.

## What it does
- Designed to provide transparent, frameless, always-on-top rendering across the Windows desktop; final multi-monitor behavior is pending manual verification.
- Renders local HTML/Canvas/WebGL animations over your desktop.
- Targeting transparent, click-through operation; pending final input verification.
- Operates locally with a minimal and documented privacy surface; pending final verification that no network, telemetry, or tracking is present.

## Available Objects (Minimal Nature Baseline)
The clean baseline candidate supports three ambient objects:
1. **Fireflies**: Six realistic fireflies flying and flashing independently.
2. **Dragonflies**: Two realistic dragonflies hovering and darting.
3. **Dandelion Seeds**: Dandelion seeds floating and drifting gently.

## Dependencies
Ohverlay is built in Python and relies on a very small set of core libraries.
- Python 3.10+
- `PySide6` (Qt for Python, including `QWebEngineView`)

## Running from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/michaelfutol/ohverlay.git
   cd ohverlay
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```
4. A system tray icon (a stylized "O") will appear. Right-click the icon to toggle the available nature overlays on or off.

## Building an Executable
You can use PyInstaller to bundle Ohverlay into a standalone executable.
1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
2. Run the build script:
   ```bash
   python build.py
   ```
3. The standalone executable will be generated in the `dist/` folder.

## Privacy & Security
Ohverlay is pending final desktop and network verification to ensure a minimal data footprint. For complete details, see [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).
