# Current Status (Audit Results)

*Last updated: Post-Consolidation Audit*

## Working Features (Verified)
- **Desktop Runtime**: Core overlay platform launches via `python main.py`
- **System Tray**: Settings and overlay toggle menu functional
- **HTML Overlays**: Rendering via QWebEngineView (transparent, click-through, always-on-top)
- **Included Overlays**: Ecosystem (dragonflies, dandelions, fireflies), Paper Lanterns, Volumetric Clouds, Sticky Notes, AI Chatbox, Exam Reviewer, Ghost Woman, Screensaver
- **Multi-monitor Support**: Enabled via `MonitorManager`
- **Hotkeys**: Global shortcuts for visibility (Ctrl+Alt+H), interactivity (Ctrl+Alt+I), and feeding (Ctrl+Alt+F)
- **Notification Modules**: Health reminders, Love Notes, Schedule Alerts with Bubble UI
- **Blue AI Assistant**: Anthropic/OpenAI backends integrated with persistent memory
- **Blue Vision**: Screen analysis via Groq
- **Integrations**: Telegram bot bridge and Webhook server functional
- **Config**: Configuration persistence at `~/.ohverlay/config.json` with legacy `.zenfish` migration
- **Build System**: PyInstaller pipeline (portable, installer, ZIP) operational
- **Testing**: 11 core module test files passing

## Incomplete / Not Yet Functional
- **Factory Backend (FastAPI)**: Scaffolded but never deployed; returns placeholder responses
- **Website**: `website/` directory is currently a placeholder
- **Domain**: `ohverlay.com` referenced throughout code but no live site exists
- **Overlay Marketplace**: `catalog.json` exists but download URLs are non-functional
- **Technical Office**: Basic sticky note exists; full standard/supervisor workflow not implemented
- **OVL Compiler**: Code exists but lacks tests; highly experimental
- **PlumberPass**: Exam reviewer functional but lacks test coverage
- **Video-to-Overlay**: Converter code exists but untested
- **OHVER Token/Credits**: Not implemented (by design)
- **Authentication**: No user accounts or login flow
- **Auto-Updater**: Downloader works locally, but manifest endpoints are not live

## Known Issues (Resolved in Cleanup)
- **README Inaccuracies**: Removed fabricated metrics (10,000+ downloads, 85% stress reduction)
- **Placeholder Branding**: Removed generic placeholders (`via.placeholder.com`) and replaced legacy support emails
- **Obsolete URLs**: Removed defunct `michaelfutol` repository links
- **Dead Code**: Purged unused scripts, scratch files, and `.txt` dumps
- **Git Ignore**: Updated to exclude caches, logs, and build artifacts
- **Docker Weak Defaults**: Hardcoded DB passwords in compose files flagged for production removal
