# Privacy & Data Handling

Ohverlay is designed to be a clean baseline candidate, pending final desktop and network verification. It contains no intentional cloud dependency.

## What is NOT collected or performed
- **No cloud requirement:** Ohverlay runs locally on your machine.
- **No telemetry:** We do not track your usage, crashes, or feature activation.
- **No API keys:** Ohverlay requires no accounts or API keys.
- **No screenshot capture:** Ohverlay does not capture your screen.
- **No screen-content analysis:** Ohverlay does not read the contents of your screen.
- **No advertising tracker:** No ads, no tracking pixels.
- **No silent network request:** The application does not communicate with external servers.
- **No employee-monitoring function:** Ohverlay is a personal tool, not a surveillance utility.
- **No inactivity tracking:** We do not track your keyboard or mouse activity.

## What is stored locally
- **Configuration:** Ohverlay stores your preferences (e.g., which overlays are active) in a local JSON file located at `~/.ohverlay/config.json`.
- **Logs:** Ohverlay writes minimal diagnostic logs (such as startup/shutdown events and errors) to `~/.ohverlay/ohverlay.log`. These logs are purely for your own local debugging and are never transmitted.

## System Interaction
- **Monitor Dimensions:** Ohverlay reads the geometry (width, height, and coordinates) of your connected monitors to correctly position its transparent overlay windows across your entire desktop workspace.
- **Autorun:** Ohverlay does not configure itself to start automatically on boot. If you wish for it to run on startup, you must configure this manually via your operating system.

## Control and Exit
- **Disabling Overlays:** You can disable individual overlays or all overlays simultaneously via the System Tray icon menu.
- **Exit:** You can completely exit the application by selecting "Quit Ohverlay" from the System Tray menu. Closing the application terminates all background processes immediately.

## Conclusion
Ohverlay is designed to respect your desktop, pending final desktop and network verification.
