# Architecture

## Current State
Ohverlay v4 is built on a hybrid architecture combining a native desktop application with web technologies.

- **Desktop Host**: Python + PySide6 (Qt). Handles OS integration, system tray, hotkeys, window management, and global config.
- **Rendering Engine**: PySide6-WebEngine (Chromium). HTML overlays are rendered as transparent, borderless, always-on-top, click-through windows.
- **Entry Point**: `main.py` instantiates the `OhverlayApp` controller.
- **Core Modules**:
  - `engine/`: Handles brain logic, multi-monitor geometry (`MonitorManager`), and LLM routing.
  - `modules/`: Feature integrations (health, schedule, updater, Telegram, Blue Vision, `overlay_manager`).
  - `ui/`: System tray and legacy skin systems.
  - `config/`: Configuration parsing and persistence.

## Target Repository Structure (Gradual Migration)
Following the consolidation directive, the repository will gradually migrate to a monorepo structure without breaking the runnable state:

```text
ohverlay/
├── apps/
│   ├── desktop/             # Current main.py and core desktop app
│   ├── technical-office/    # Future supervisor dashboard apps
│   └── website/             # Future public website
├── packages/
│   ├── overlay-runtime/
│   ├── office-coordination/
│   ├── blue-ai/
│   ├── privacy-consent/
│   ├── shared-ui/
│   └── ovl/                 # Current OVL compiler
├── overlays/
│   ├── productivity/
│   ├── nature/
│   ├── ambient/
│   ├── interactive/
│   └── learning/
├── services/
│   ├── messaging/
│   ├── reporting/
│   ├── supervisor-dashboard/
│   ├── marketplace/
│   └── updater/
├── website/                 # Temporary root location for website
├── supabase/
│   ├── migrations/
│   ├── seed/
│   └── tests/
├── docs/
├── releases/
└── .github/workflows/
```
