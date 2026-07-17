# OHVERLAY v4.0 Installation Guide

## Setup Installer

- `Ohverlay-v4.0-Setup.exe` installs per-user to `%LOCALAPPDATA%\Programs\Ohverlay`.
- Administrator approval is not required for the standard install path.
- The installer is unsigned, so Windows SmartScreen may still show a warning.

## Portable Build

- Keep the entire `dist\Ohverlay\` folder together.
- Do not copy `Ohverlay.exe` by itself; it must stay beside `_internal\python311.dll` and the rest of the bundled files.
- For office-PC testing, zipping the full `dist\Ohverlay\` folder is the safest portable distribution method.

## First Launch

Right-click the tray icon to open:

- `Overlays`: Sticky Note, Blue AI Chat, Exam Reviewer, Aurora, Fairy & Dandelion, Manta Ray, Ghost Woman
- `Sanctuary Mode`
- `Notifications`
- `Integrations`

Global hotkeys:

- `Ctrl+Alt+H`: Toggle all overlays
- `Ctrl+Alt+S`: Toggle Sanctuary mode

## Troubleshooting

**"Windows protected your PC"**

Click `More info` then `Run anyway`. This happens because the build is unsigned.

**"Failed to load Python DLL"**

You copied only `Ohverlay.exe`. Copy or extract the full `dist\Ohverlay\` folder instead.

**Overlays menu appears but nothing opens**

Rebuild with `PySide6-WebEngine` installed. HTML overlays depend on Qt WebEngine.

**App is blocked on a managed office PC**

No-admin install does not bypass SmartScreen, Defender, AppLocker, or company execution policy. An unsigned build can still be blocked by IT policy.
