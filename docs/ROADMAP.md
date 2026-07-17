# Ohverlay Roadmap

This roadmap governs the priority sequence for Ohverlay development, following the consolidation directive.

## 1. Stable Desktop Runtime [Current Priority]
- Baseline the existing multi-monitor overlay system.
- Clean up dead code, redundant branches, and historical artifacts.
- Ensure the portable and installer builds pass validation consistently.

## 2. Technical-Office Sticky Notes & Reporting
- Evolve the existing sticky note system.
- Add roles (Standard User vs Supervisor).
- Build local-network communication, elapsed timers, and task assignment logic.

## 3. Privacy and Consent Architecture
- Formalize the explicit consent requirements for Blue AI Vision.
- Build transparent UI indicators when screen context or local memory is active.

## 4. Overlay Package Manager
- Decouple overlays from the core binary.
- Allow dynamic downloading, installing, enabling, and disabling of overlay packages.

## 5. Website and Marketplace
- Build a central catalog website at `ohverlay.com`.
- Host metadata and download links for the overlay package manager.

## 6. Optional User Accounts
- Implement Supabase authentication.
- Keep desktop functionality usable without accounts, gating only premium marketplace or cloud sync features.

## 7. Automated Releases
- Set up GitHub Actions for CI/CD.
- Automatically build PyInstaller executables on tags.
- Publish releases to GitHub and update the auto-updater manifests.

## 8. Internal Ohver Credits and Entitlements
- Build an internal points system for marketplace redemption.
- Lay the groundwork for creator rewards.

## 9. Future OHVER Feasibility Study
- Explore the mechanics of a fixed-supply (1,000,000) ecosystem credit.
- Ensure strict compliance with the Product Doctrine (no smart contracts, no crypto payments).
