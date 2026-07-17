# Technical Office Architecture

The Technical Office lane within Ohverlay is designed to support coordination within engineering teams, design studios, and remote offices, focusing strictly on workflow and instruction delivery without employee surveillance.

## Core Capabilities

### 1. Sticky Notes & Timed Instructions
- **Draggable Overlays:** Floating sticky notes that reside on the desktop.
- **Rich Text Support:** Basic formatting for technical instructions.
- **Timers:** Support for both countdown timers (e.g., "Review due in 30 mins") and elapsed timers (e.g., "Time spent on ticket").

### 2. Status & Acknowledgements
- **Read Receipts:** Visual indicators showing when a staff member has opened an instruction overlay.
- **Acknowledgements:** Explicit buttons for staff to confirm they have read and understood a directive.

### 3. Local-Network Coordination (Testing/Planned)
- Instructions and sticky notes can be synchronized over local shared folders, bypassing the need for an external cloud server.
- Support for offline or strict internal-network environments (air-gapped offices).

### 4. Roles
- **Standard User (Staff):** Receives instructions, interacts with timers, and sends acknowledgements.
- **Supervisor:** Dispatches instructions, monitors task completion statuses, and views the Supervisor Dashboard.

## Privacy Boundaries
- The Technical Office modules **do not** collect active window titles, keystrokes, or background process data.
- Coordination relies on explicit status updates (e.g., clicking "Acknowledge") rather than passive data mining.
