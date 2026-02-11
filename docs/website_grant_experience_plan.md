# OHVERLAY Website Experience Plan (Grant-Ready)

This plan defines how the public website can match the emotional quality of Uno while staying safe, ethical, and performant for grant demos.

## Goals
- Showcase the same calm identity as the desktop app.
- Demonstrate technical maturity for grant reviewers.
- Keep privacy and trust controls explicit.

## Experience Targets
1. **Hero section with Uno-quality motion**
   - Browser-native fish simulation inspired by desktop movement profiles.
2. **Dual Betta demo mode**
   - User-toggle preview for 1 or 2 bettas with independent palettes.
3. **Ambient effects controls**
   - Leaves, quotes, and calm overlays are user opt-in and clearly labeled.
4. **Accessibility first**
   - Reduced motion mode and keyboard controls.

## Technical Direction
- Use a web renderer (Canvas/WebGL) separate from PySide runtime.
- Keep deterministic animation ticks and capped particle counts.
- Add explicit performance tiers:
  - Tier A: Full visuals (desktop GPUs)
  - Tier B: Reduced particles/effects (integrated GPUs)
  - Tier C: Solo Uno + minimal effects (low-resource devices)

## Grant-Visible Proof Points
- FPS stability under common laptop hardware.
- Memory budget and CPU budget thresholds by tier.
- Privacy posture: no silent tracking, opt-in analytics only.
- Reproducible QA checklist with pass/fail evidence.

## Demo Readiness Checklist
- [ ] Hero fish motion validated against desktop reference clips.
- [ ] Dual Betta toggle stress-tested for 15 minutes.
- [ ] Reduced motion + accessibility checks completed.
- [ ] Privacy and data-use statement reviewed.
- [ ] Fallback behavior validated on low-resource devices.

## Rollout Note
Website public launch remains gated by existing copyright and governance controls.
