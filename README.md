# Ohverlay

**Ohverlay is a privacy-conscious desktop overlay platform for productivity, technical-office coordination, ambient digital companions, learning tools, and user-installable overlay experiences.**

*Useful information and living experiences, gently layered over your workspace.*

---

## Executive Overview

Ohverlay solves the problem of disruptive digital environments by placing useful, calm, and context-aware tools directly onto your desktop without requiring you to switch away from your active work. Unlike traditional widgets or aggressive notification systems, Ohverlay operates as a transparent, click-through layer that floats above your wallpaper and behind (or alongside) your open windows.

Built with local-first, privacy-conscious principles, Ohverlay does not monitor employees silently and requires explicit consent for any screen-awareness features. It serves as a unified ecosystem blending technical-office coordination, personal productivity, learning aids, and ambient digital companions.

## Product Areas

### Technical Office
Coordinate team operations with clear, non-disruptive overlays:
- **Verified:** Draggable sticky notes, countdown timers, elapsed timers, deadlines.
- **Implemented (Testing):** Local-network shared-folder coordination, staff-to-supervisor reporting, opened and acknowledged status.
- **Planned:** Supervisor dashboard, consent-aware workplace deployment rules.

### Productivity
Tools to keep you focused and organized on modest hardware:
- **Verified:** Notes, timers, reminders, break prompts, schedule overlays.

### Living and Ambient Overlays
Bring your workspace to life with responsive, non-distracting motion:
- **Verified:** Dragonflies, dandelions, fireflies, ladybugs, aquarium creatures, volumetric clouds, paper lanterns.
- **Features:** Click-through behavior, multi-monitor motion, configurable transparency.

### Learning
Passive educational tools integrated into your daily workflow:
- **Verified:** Exam-review overlays (PlumberPass prototype).
- **Planned:** Passive quizzes, study reminders, educational packs.

### Blue AI
An optional, privacy-respecting intelligence layer:
- **Verified:** Optional assistant, user-controlled memory.
- **Testing:** Explicitly authorized screen awareness.
- **Core Principle:** Local-first operation where practical. No silent monitoring, no hidden employee surveillance.

### Marketplace and Creator Ecosystem
A growing library of installable experiences:
- **Prototype:** Installable overlay packages, free packs, preview/install workflows.
- **Planned:** Creator entitlements, paid packs.

## Why Ohverlay Matters

Ohverlay delivers calm, non-disruptive information delivery for engineering offices, remote teams, and students. By running efficiently on modest hardware, it provides accessible productivity support and creates future opportunities for Filipino developers and digital creators. Crucially, it serves as an ethical, privacy-conscious alternative to intrusive monitoring software, ensuring staff coordination never crosses into surveillance.

## Current Status

| Area | Status | Evidence | Limitations |
| ---- | ------ | -------- | ----------- |
| **Desktop Runtime** | Verified | Application launches, multi-monitor geometry works, transparent PySide6 windows render correctly. | Heavy DOM manipulation can spike CPU on low-end hardware. |
| **Living Overlays** | Verified | Dragonflies, Dandelions, Fireflies, Lanterns load and animate. | Interactions (feeding) require hotkeys rather than direct clicks. |
| **Productivity** | Verified | Sticky notes, timers, reminders load. | Network sync for notes is in testing. |
| **Technical Office** | Testing | Staff-to-supervisor reporting scaffolded. | Full supervisor dashboard UI incomplete. |
| **Blue AI** | Prototype | Anthropic/Groq integration exists. | Requires user-provided API keys; local models not yet optimized. |
| **Marketplace** | Prototype | Local catalog parsing works. | Remote downloads and authentication not yet live. |

## Architecture

At its core, Ohverlay uses a PySide6 frameless window containing a QWebEngineView. The Python backend handles OS-level geometry, global hotkeys, AI bridging, and configuration persistence, while the frontend renders standard HTML/CSS/JS overlays (using a custom vanilla JS engine).

- **Desktop Runtime:** PySide6, Python 3.11+
- **Overlay Engine:** HTML5, CSS3, Vanilla JS
- **AI Bridge:** LiteLLM / Custom Blue AI router
- **Future Backend:** Supabase (planned for Marketplace/Updates)

For deeper technical details, read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Privacy and Ethics

Ohverlay is fundamentally built on consent:
- **Local-first defaults:** Your configuration and logs stay on your machine.
- **Explicit consent:** Screen analysis requires manual authorization.
- **No silent monitoring:** We reject hidden employee surveillance and silent screenshots.
- **User control:** You control your data and update behavior.

Read our full [PRIVACY.md](PRIVACY.md) and [docs/ETHICAL_DESIGN.md](docs/ETHICAL_DESIGN.md) for details.

## Installation and Development

### Requirements
- **OS:** Windows 10/11
- **Runtime:** Python 3.11.9+

### Development Setup
```powershell
git clone https://github.com/michaelfutol/ohverlay.git
cd ohverlay
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Running the App
```powershell
python main.py
```

### Running Tests
```powershell
pytest tests/
```

### Building (Portable & Installer)
```powershell
python build.py
```

## Roadmap

1. Canonical repository stabilization
2. Technical-office workflow restoration
3. Privacy and consent framework
4. Overlay package manager
5. Website and marketplace
6. Optional accounts and entitlements
7. Automated builds and releases
8. Creator ecosystem
9. OHVER feasibility research

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed planning.

## Governance and Contribution

We welcome contributions that align with our ethical principles and technical standards.
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [GOVERNANCE.md](GOVERNANCE.md)

## Licensing and Ownership

**Copyright © FutolTech Engineering & Project Systems**

*All Rights Reserved.*

Ohverlay is currently provided under a proprietary/source-available notice. Access to this source code does not grant authorization for redistribution, commercial reuse, or repackaging without explicit permission. Licensing may change in a future public release.

See [LICENSE](LICENSE) for the full notice.
