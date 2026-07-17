# Repository Quality Audit

## Overview
This repository underwent a massive purification to achieve the "Minimal Nature Baseline." All untracked, experimental, or unrelated files were removed to prepare the repository for review by external partners, granting agencies, and collaborators.

## Status of Key Quality Metrics

### 1. Extraneous Files and "Scratch" Code
- **Status:** Purged.
- All temporary text files, unlinked HTML experiments, and old scripts have been removed.

### 2. Leaked Secrets and Hardcoded Credentials
- **Status:** Verified Clean.
- The `config/settings.py` was rewritten to remove placeholder fields for API keys (e.g., Anthropic, OpenAI, Telegram).
- A git history rewrite (orphan branch reset) was performed to permanently destroy old commits that contained leaked keys. (Note: Any keys previously committed were also explicitly rotated/revoked by the author).

### 3. Orphaned or Incomplete Features
- **Status:** Purged.
- Incomplete features such as the `factory` web dashboard, `plumberpass` compiler, AI Brain integration, Webhooks, and Health/Schedule modules were fully deleted.

### 4. Legacy Branding
- **Status:** Purged.
- All references to "ZenFish," "Project Aether," "ikel-eidra," and obsolete URLs have been destroyed. The product is exclusively identified as **Ohverlay**.

### 5. Dependency Cleanliness
- **Status:** Minimal.
- Only the absolutely essential requirements (`PySide6`) remain.

## Conclusion
The repository now accurately reflects the core goal of Ohverlay: a clean, lightweight, offline nature overlay runtime.
