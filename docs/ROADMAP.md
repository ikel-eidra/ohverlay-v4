# Roadmap

The current phase is entirely focused on stability and purification. No new features will be added until the minimal baseline is verified and trusted.

## Phase 1: Purification and Baseline (Current)
- [x] Strip out all experimental, AI, and network features
- [x] Eliminate legacy branding (ZenFish, Aether, etc.)
- [x] Establish a single, canonical repository (`michaelfutol/ohverlay`)
- [x] Create the Minimal Nature Baseline (Fireflies, Dragonflies, Dandelions only)
- [x] Rewrite history via an orphan branch to erase messy commits and leaked secrets
- [ ] Manual visual verification of the baseline build

## Phase 2: Performance and Packaging
- Update PyInstaller build scripts for the minimal baseline
- Add automated CI/CD for release builds
- Reduce memory footprint of QWebEngine by profiling WebGL rendering
- Optimize canvas rendering inside HTML overlays

## Phase 3: Future Expansion (Strictly Gated)
If and only if Phase 2 is complete, we may consider re-introducing features from the purged repository, strictly one by one, ensuring zero regressions to stability or privacy.
- Restore the Inactivity/Screensaver trigger functionality.
- Re-evaluate the Fish/Ecosystem engine.
- Introduce interactive non-distracting objects.
