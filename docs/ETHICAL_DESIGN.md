# Ethical Design and Privacy Framework

Ohverlay is designed around the principle of **calm technology** and **user sovereignty**. We reject the normalization of workplace surveillance and intrusive digital environments. 

## 1. Local-First Operation
Ohverlay executes primarily on the user's local machine. 
- Configuration settings (`config.json`), activity logs, and technical office state are stored locally.
- Ohverlay does not enforce cloud synchronization for core features.

## 2. No Silent Monitoring
Workplace coordination tools often blur the line between productivity and surveillance. Ohverlay strictly maintains this boundary:
- **No Keystroke Logging:** Ohverlay does not capture keyboard input outside of explicitly focused overlay forms or registered global hotkeys.
- **No Hidden Screenshots:** The application will never silently capture the user's screen.
- **No Background Process Mining:** Ohverlay does not scan background processes or report active window usage to supervisors.

## 3. Explicit Consent for AI
When utilizing the Blue AI features (e.g., Anthropic or Groq integrations):
- Users must explicitly provide their own API keys.
- Screen awareness features (Blue Vision) require a manual trigger (e.g., a hotkey or button press) to capture and analyze the screen.
- Users are notified when their screen or context is being analyzed by an external model.

## 4. Calm and Accessible
- Overlays are designed to be click-through and non-disruptive, preventing notification fatigue.
- The software is optimized to run on modest hardware, ensuring accessibility for users without high-end workstations.
