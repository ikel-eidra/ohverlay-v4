<div align="center">

# OHVERLAY v4.0

[![Version](https://img.shields.io/badge/version-4.0.0-purple.svg?style=for-the-badge)](https://github.com/michaelfutol/ohverlay-v4)
[![Python](https://img.shields.io/badge/python-3.10+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg?style=for-the-badge)](https://wiki.qt.io/Qt_for_Python)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Maintainer](https://img.shields.io/badge/maintainer-Michael%20Futol-9333EA.svg?style=for-the-badge)](https://github.com/michaelfutol)

**A professional desktop overlay platform**

*Calm your workspace, ethically.*

</div>

---

## ✨ What is Ohverlay?

**Ohverlay** is an ethical AI desktop companion ecosystem. It renders fully transparent, click-through HTML overlays directly on your desktop across multiple monitors. 

### Core Product Lanes
1. **Technical Office**: Professional coordination and local communication via sticky notes and timers.
2. **Desktop Living Overlays**: Ambient, non-distracting environmental life (e.g., Dragonflies, Fireflies).
3. **Productivity Overlays**: Workspace enhancement, exam reviewers, and schedule reminders.
4. **Blue AI**: Ethical, user-controlled artificial intelligence with optional screen awareness (Blue Vision).
5. **Marketplace**: A central catalog for discovering and installing overlay packages.
6. **Future OHVER Ecosystem**: Internal entitlement architecture based on the "OHVER" concept.

---

## 🚀 Key Features

| Feature | Description | Tech |
|---------|-------------|------|
| 🖥️ **Multi-Monitor** | Seamless overlay rendering across 2-3+ screens | PySide6 |
| 👆 **Click-Through** | Works behind your windows | Transparent Qt Widgets |
| 🌐 **HTML Overlays** | Build overlays with standard web tech | QWebEngineView |
| 🧠 **Blue AI** | Optional AI assistant with memory | LLM (Anthropic/OpenAI) |
| 👁️ **Blue Vision** | Screen analysis via Groq | Vision APIs |
| 🔔 **Notifications** | Health reminders, Love Notes, Schedule Alerts | State machine |

---

## 🧠 Technical Architecture

Ohverlay v4 is built on a hybrid architecture combining a native desktop application with web technologies.

- **Desktop Host**: Python + PySide6 (Qt). Handles OS integration, system tray, hotkeys, window management, and global config.
- **Rendering Engine**: PySide6-WebEngine (Chromium). HTML overlays are rendered as transparent, borderless, always-on-top, click-through windows.
- **Entry Point**: `main.py` instantiates the `OhverlayApp` controller.

For more details, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📥 Installation

### Quick Start (Windows)

```bash
# 1. Clone the repository
git clone https://github.com/michaelfutol/ohverlay-v4.git
cd ohverlay-v4

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Ohverlay
python main.py
```

### Portable Distribution

For Windows testing, especially on office PCs:

1. Run `build_installer.bat` to create a per-user installer in `installer_output\`.
2. Or run `build_portable_zip.bat` to generate a portable ZIP bundle.

### Configuration

Configuration is managed via `~/.ohverlay/config.json`.
You can access settings from the System Tray icon.

---

## 🎮 Usage

### Hotkeys

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+Alt+H` | Toggle Overlays | Show or hide all active overlays |
| `Ctrl+Alt+I` | Toggle Interactivity | Make overlays clickable vs click-through |
| `Ctrl+Alt+F` | Interact | Trigger context-specific interactions |

### System Tray

Right-click tray icon for:
- Overlays toggle
- Notifications settings
- Integrations
- Quit

---

## Bundled Overlays

- Ecosystem (Dragonflies, Dandelions, Fireflies)
- Paper Lanterns
- Volumetric Clouds
- Sticky Notes
- AI Chatbox
- Exam Reviewer
- Ghost Woman
- Screensaver

---

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest tests/test_config.py
python main.py
```

---

## Documentation

See the `docs/` directory for full details on architecture, product doctrine, and current status:
- [Canonical Repository Policy](docs/CANONICAL_REPOSITORY.md)
- [Current Status](docs/CURRENT_STATUS.md)
- [Product Doctrine](docs/PRODUCT_DOCTRINE.md)
- [Roadmap](docs/ROADMAP.md)

---

## License & Distribution Status

See [LICENSE](LICENSE). Builds are currently unsigned, so Windows reputation prompts are expected until code signing is added.
