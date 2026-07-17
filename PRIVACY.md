# Privacy Policy

Ohverlay is built on a foundation of local-first architecture and explicit user consent. We believe that workplace coordination tools should not double as surveillance software.

## Data Storage
- **Local Data:** By default, all configuration settings, logs, and activity records are stored locally on your machine in the `~/.ohverlay` directory.
- **Optional Cloud Data:** In the future, optional cloud integration (e.g., for the Marketplace or synchronized sticky notes) will require an explicit account creation.

## AI and Screen Analysis
- **Optional AI Providers:** Ohverlay's Blue AI assistant relies on external APIs (like Anthropic or Groq). You must manually configure these with your own API keys. Prompts sent to these APIs are subject to the respective provider's privacy policies.
- **Screenshot Permissions:** Ohverlay will **never** take silent screenshots. Screen analysis features require explicit, manual authorization for every action. 

## Workplace Deployments
- **Supervisor Functions:** The Technical Office modules support coordination (e.g., sending instructions, receiving acknowledgments). This is strictly for operational alignment.
- **No Hidden Monitoring:** There are no mechanisms for supervisors to silently monitor employee screens, keystrokes, or active applications. Ohverlay maintains a clear distinction between staff coordination and surveillance.

## Updates and Network Requests
- **Update Checks:** Ohverlay may periodically ping a manifest URL to check for updates. This transmits only basic request headers. You have control over update behavior.
- **User Deletion and Export:** Because data is stored locally, deleting the `~/.ohverlay` directory effectively purges your user data. Future cloud-connected features will include dedicated export and account deletion options.

## What is Implemented vs. Planned
- **Implemented:** Local-first configuration, manual AI key integration, local logging.
- **Planned:** Marketplace accounts, local-network coordination sharing.
