# Contributing to Ohverlay

Thank you for your interest in contributing to Ohverlay! To maintain the project's high standards of privacy, calm design, and codebase stability, we ask all contributors to adhere to the following guidelines.

## Branch Policy
- The `main` branch is the authoritative source of truth.
- All development must happen in short-lived feature branches.
- Branch names should be descriptive (e.g., `feat/sticky-notes-sync`, `fix/tray-menu-crash`, `chore/cleanup-assets`).

## Pull Request Expectations
1. **Pull Request Template:** Ensure you fill out the provided PR template.
2. **No Unsupported Claims:** Do not include fake metrics, exaggerated claims, or untested assumptions in documentation or PR descriptions.
3. **No Secrets:** Never commit API keys, passwords, or personal credentials. Double-check your diffs before pushing.
4. **Privacy-Impact Review:** If your PR introduces network calls, tracking, or local data access, explicitly detail this in your PR description. Ohverlay rejects silent monitoring.

## Test Requirements
- **Pass the Baseline:** All PRs must pass the existing test suite (`pytest tests/`).
- **Write New Tests:** New modules or features must be accompanied by appropriate unit tests.
- **Manual Verification:** Document the manual smoke testing you performed, identifying the OS and Python version used.

## Code Standards
- Follow standard PEP 8 naming conventions and formatting for Python code.
- Ensure HTML/CSS/JS overlays use clean, vanilla code where possible to maintain low overhead.
- Use clear, descriptive variable names. Avoid AI-generated filler comments or joke filenames.

## Documentation Standards
- Ensure all new features are factually documented.
- Differentiate clearly between what is *verified*, *prototype*, and *planned*.
- Respect the professional tone of the repository.

## Overlay Submission Standards
If you are submitting a new overlay package to the marketplace ecosystem:
- Keep asset sizes optimized.
- Do not include malicious or heavy third-party tracking scripts.
- Ensure the overlay gracefully handles multi-monitor scaling.
- Follow the package format guidelines outlined in `docs/OVERLAY_PACKAGE_FORMAT.md`.
