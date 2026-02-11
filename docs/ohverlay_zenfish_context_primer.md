# Ohverlay / ZenFish Context Primer

This document captures the current product and engineering direction for the desktop overlay so future contributors can move quickly without destabilizing the core experience.

## 1) Product Identity & Vision

- **Runtime app name:** ZenFish Overlay.
- **Ecosystem direction:** Ohverlay / Overlay Ecosystem.
- **Core promise:** Calm, always-on, desktop-native companion fish overlay with monitor-aware motion, non-intrusive bubbles, and optional integrations.

## 2) Current App Baseline

### Architecture
- `main.py`: application boot, subsystem wiring, loop, tray, and module orchestration.
- `engine/brain.py`: single Betta behavior.
- `engine/school.py`: boids logic for multi-fish schooling.
- `engine/aquarium.py`: transparent per-monitor rendering sectors.
- `ui/*.py`: skins and bubble visuals.
- `engine/llm_brain.py`: Anthropic/OpenAI text generation and optional vision foraging.
- `modules/*.py`: health, news, schedule, love notes, Telegram, webhook, updater.
- `config/settings.py`: JSON-persisted local config.
- `utils/logger.py`: hardened logging for regular and frozen builds.

### Recently integrated capabilities
1. Hardened logger behavior for frozen builds and temp-dir failures.
2. Motion profile system (`prototype`, `realistic_v2`) with telemetry-to-renderer coupling.
3. Optional vision foraging via OpenAI screenshots and async analysis.
4. Wider school roaming over monitor space.
5. Discus/tetra visibility and turn hysteresis tuning to reduce jitter/invisibility.
6. Company metadata integration for runtime and Windows EXE version resources.
7. Auto-update downloader skeleton and support email placeholder in config.

## 3) Business & Brand Context

- **Company identity:** Futol Ethical Technology Ecosystems.
- **Location for metadata context:** Sta. Magdalena, Sorsogon.
- Maintain calm, ethical, non-intrusive UX.
- Preserve trust: no silent execution of downloaded installers.

## 4) Perfection Criteria (Operational)

A candidate is considered "perfection" only when these pillars stay balanced:
1. Visual believability.
2. Behavioral realism.
3. Reliability.
4. Commercial readiness.
5. Ethical product integrity.

## 5) Explicit Product Goals

- **A — Companion Core:** Delightful, stable Betta default; visible, consistent schooling species.
- **B — Ethical Engagement:** Calm contextual bubbles and future opt-in rewards only.
- **C — Portability:** Strong Windows channel with macOS parity path.
- **D — Monetization Readiness:** Paid features/updates without trust-breaking behavior.
- **E — Governance:** Privacy-aware analytics with observability.

## 6) Current Constraints / Risks

1. Runtime GUI dependency variance in headless or restricted environments.
2. Incomplete updater security (signature verification pipeline missing).
3. Vision foraging privacy/safety controls need stronger policy surface.
4. macOS packaging maturity (sign/notarization) needs dedicated work.
5. School distribution requires long-run visual QA to catch clustering pathologies.

## 7) Recommended Milestones (Order)

1. **Lock Stable v1** with critical fixes only.
2. **Perfection branch** (`perfection-v2`) for high-iteration realism experiments.
3. **Rendering + behavior QA pass** with repeatable visual checklist.
4. **Updater hardening** with manifest validation, checksum/signature checks, channeling.
5. **Minimal ethical analytics layer** (opt-in, key events only).
6. **Commercial packaging** and release readiness.

## 8) Product Guardrails

1. No silent trust-breaking auto behaviors.
2. User agency first for vision/analytics/update settings.
3. Graceful fallback for logger, LLM, network, and updater outages.
4. Preserve low-resource performance budgets.

## 9) Distribution Model

- **Current stage:** private prelaunch distribution only (controlled family/team rollout).
- **Windows (primary):** PyInstaller, accurate metadata, installer + portable fallback.
- **macOS (secondary):** signed/notarized distribution with tray/overlay validation.
- **Browser extension:** lightweight companion and desktop acquisition channel.
- **Android/iOS:** companion-first (sync/status/rewards), wallpaper/widget later.
- **Public website launch gate:** hold until copyright notices, channel controls, and release governance are fully in place.

## 10) Minimal Analytics Blueprint

### Event names
- `app_first_launch`
- `session_start`
- `session_end`
- `species_switch`
- `vision_foraging_toggled`
- `llm_provider_active`
- `update_check`
- `update_downloaded`
- `error_nonfatal`

### Core metrics
- DAU/WAU/MAU.
- D1/D7 retention.
- Crash-free session rate.
- Update adoption lag by version.
- Premium/value feature adoption.

## 11) Definition of Done for a Perfection Candidate

A release candidate is acceptable only if:
- Turning is smooth with no recurring flip jitter.
- Discus/tetra rendering is stable on common monitor setups.
- Startup resilience is high in restricted environments.
- Update path is secure and user-controlled.
- Telemetry privacy posture is documented and opt-in.
- Branding and support contact are fully aligned.

## 12) Immediate To-Do Handoff Checklist

- [ ] Replace placeholder support email with production inbox.
- [ ] Set production `update_manifest_url`.
- [ ] Add installer hash/signature validation before ready state.
- [ ] Add update notes UX surface (tray or modal).
- [ ] Run 30–60 minute school behavior tests.
- [ ] Create stable tag and branch policy docs.
- [ ] Publish privacy + telemetry policy for app/site.
- [ ] Create release playbook (build, smoke test, publish, rollback).

## 13) Operating Principle

Protect the stable emotional core first: calm + trust. Iterate realism, growth, and monetization in controlled layers that do not compromise that foundation.
