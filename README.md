# Ohverlay: Ethical Desktop Overlay Companion

![Hero Image: Uno the Purple Betta](https://via.placeholder.com/1200x400/9333EA/C084FC?text=Uno+the+Purple+Betta+Swimming+Gracefully)

Ohverlay is a calm, semi-transparent desktop overlay companion ecosystem. The current runtime experience is **ZenFish Overlay**: a lifelike betta fish that swims across your monitor space without interrupting your workflow.

> Focus right now: **Ohverlay + ZenFish muna** — relaxation, practicality, and ethics first.

![Demo GIF: Zenfish in Action](https://via.placeholder.com/800x450/000000/FFFFFF?text=Zenfish+Swim+Demo+GIF)

## Overview
ZenFish is designed as a quiet companion for productivity-heavy workflows. It gives ambient presence, subtle supportive prompts, and natural fish behavior while staying non-intrusive and user-controlled.

## Current Key Features
- **Lifelike Betta Rendering**: Uno-inspired purple betta styling with procedural animation and glow.
- **Multi-Monitor Overlay**: Smooth movement across one or more screens.
- **Click-Through UX**: Transparent overlay that does not block your normal desktop interaction.
- **Symbolic Pellet Interaction**: `Ctrl+Alt+F` drops pellets where the user points, and fish responds while **continuing to swim** (no hard stop/feed dependency).
- **Calm Integrations**: Bubble-based modules for health, schedule, love notes, and news.
- **Optional LLM Brain**: Anthropic/OpenAI support with graceful fallback behavior when unavailable.

![Screenshot: Multi-Monitor Swim](https://via.placeholder.com/800x450/9333EA/C084FC?text=Multi-Monitor+Swim+Screenshot)

## Installation (Development)
```bash
git clone https://github.com/ohverlay/ohverlay.git
cd ohverlay
pip install -r requirements.txt
python main.py
```

## Portable Runtime Goal
For public users, distribution targets:
1. Download ZIP bundle from official site.
2. Extract and run `start.bat`.
3. No admin prompts for standard usage.

## Usage
- **Drop Pellets**: `Ctrl+Alt+F` (symbolic, stress-relief style interaction).
- **Toggle Sanctuary**: `Ctrl+Alt+S`.
- **Toggle Visibility**: `Ctrl+Alt+H`.
- **Customize**: Update local config (`~/.zenfish/config.json`) or tray options.

## Product Guardrails (Non-Negotiable)
- Local-first defaults and graceful fallbacks.
- Opt-in controls for sensitive features.
- No trust-breaking auto-behavior (ex: silent executable runs).
- Ethical, non-intrusive attention design.

## Tech Stack
- **Python + PySide6 (Qt)** for transparent overlay windows and rendering.
- **Procedural animation** (sine/perlin + steering dynamics) for movement realism.
- **Modular integration layer** for communication and productivity features.

## Roadmap Snapshot
- **v1.x hardening**: behavioral smoothness, visual QA, updater hardening.
- **v2 direction**: richer bubble interactions, privacy-safe analytics opt-in, deeper ecosystem integration.
- **Long-term**: companion channels (extensions/mobile) without replacing desktop core.

## Points for Coders (Pass-On Notes)
- Keep CPU budget disciplined for low-end office PCs.
- Continue improving fish physics realism and fin-body coupling.
- Keep bubble UX subtle (non-disruptive, contextual).
- Build API/MCP/SDK connectors incrementally and safely.
- Keep security and privacy posture transparent and opt-in.
- Avoid branded ad assets until official client agreements.

## Product Direction & Handoff
For implementation-grounded context (identity, milestones, risks, guardrails, and release criteria), see:

- [`docs/ohverlay_zenfish_context_primer.md`](docs/ohverlay_zenfish_context_primer.md)

## Contributing
Pull requests are welcome. Keep changes calm-by-default, ethically aligned, and performance-aware.

## License
MIT — free to use and modify.

**Ohverlay & ZenFish**: calm your workspace, ethically.


Official site: https://ohverlay.com
