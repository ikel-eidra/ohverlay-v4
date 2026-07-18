# Manual Visual Verification Checklist

Before the `chore/minimal-nature-baseline` branch can be merged into `main`, the following manual visual verification steps MUST be performed locally by the author to ensure rendering integrity and stability.

## Prerequisites
1. Build the application locally, or run `python main.py` directly from the terminal.
2. Have all multiple monitors connected, if applicable.

## Verification Steps

### 1. Startup and Console
- [x] Ensure that starting `main.py` produces **no immediate Python crash or traceback errors**.
- [x] Ensure that the system tray icon appears correctly (a stylized 'O').
- [x] Ensure the tooltip on the tray icon reads exactly: "Ohverlay — Minimal Nature Baseline".

### 2. Tray Menu Interaction
- [x] Right-click the tray icon and verify that only "Nature Overlays", "Overlay Settings", "Toggle All Overlays", "Debug: Show Canvas Extent", and "Quit Ohverlay" are present.
- [x] Verify that no AI, Telegram, Webhook, Sanctuary, or Aquarium options are present in the menu.
- [x] Verify that checking and unchecking overlays properly adds and removes checkmarks in the menu.

### 3. Rendering Integrity (Transparency)
- [x] Activate the **Dragonflies** overlay.
- [x] Verify that the background remains **100% transparent**. There should be no white or black backgrounds, no scrollbars, and no window borders.
- [x] Verify that the dragonflies fly around the screen **without leaving visual trailing boxes or artifacts**.
- [x] Verify that the desktop behind the overlay remains completely clickable (click-through works as expected).

### 4. Overlays
- [x] Activate **Fireflies**. Ensure fireflies blink and move without rendering issues.
- [x] Activate **Dandelions**. Ensure seeds float smoothly across the screen without rendering issues.
- [x] Verify that enabling multiple overlays at once does not crash the application.

### 5. Exit
- [x] Select "Quit Ohverlay" from the tray menu.
- [x] Verify that all overlays disappear immediately.
- [x] Verify that the terminal process exits cleanly without hanging.

## Sign-Off
Once all steps above are confirmed successful, the cleanup can be considered complete, screenshots can be taken for the README, and the branch can be merged into `main`.

**Status:** ALL VERIFIED AND PASSED LOCALLY BY MICHAEL FUTOL (2026-07-18).
