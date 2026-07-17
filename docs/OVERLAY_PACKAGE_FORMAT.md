# Overlay Package Format

Ohverlay supports a marketplace ecosystem of installable overlays. To maintain security, performance, and cross-platform compatibility, all overlay packages must adhere to the standard format.

## Structure (Prototype)

An overlay package is typically a compressed directory (e.g., a `.zip` file or a specific `.ovl` extension) containing the following structure:

```text
my-overlay/
├── index.html       # Entry point for the overlay
├── style.css        # Styles specific to the overlay
├── script.js        # Logic (Vanilla JS preferred)
├── manifest.json    # Package metadata
└── assets/          # Images, audio, or specific fonts
```

## `manifest.json` Specification

The `manifest.json` file describes the overlay and dictates its capabilities.

```json
{
  "id": "com.creator.my-overlay",
  "name": "My Cool Overlay",
  "version": "1.0.0",
  "author": "CreatorName",
  "description": "A calm, ambient overlay for your desktop.",
  "type": "ambient", 
  "entry": "index.html",
  "permissions": []
}
```

## Security Constraints
- **External Resources:** Overlays should ideally bundle all assets locally. Fetching external scripts (e.g., CDN tracking scripts) may be blocked by the Ohverlay security policy.
- **Node Integration:** Node.js integration within the QWebEngineView is disabled. Overlays must rely on standard browser APIs.
- **Local Storage:** Overlays can use local storage, but persistent config changes should route through the Ohverlay bridge API.

*Note: The Marketplace and package installation workflows are currently in the prototype stage.*
