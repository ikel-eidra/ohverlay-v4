# Security Policy

## Supported Versions

Currently, Ohverlay is in a pre-release development phase. Only the latest commit on the `main` branch is actively evaluated for security updates.

| Version | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |
| legacy  | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within Ohverlay, please contact the maintainer directly. **Do not publicly disclose vulnerabilities** until they have been resolved.

- **Contact:** Open a private security advisory on GitHub or contact the maintainer directly if an email is provided.

We will attempt to review and acknowledge receipt of the vulnerability report promptly. Note that as a pre-release project, we do not currently offer a strict SLA for remediation, but we prioritize critical privacy and local-escalation issues.

## Security Architecture & Expectations

### Sensitive Data Handling
Ohverlay stores configuration data locally in `~/.ohverlay/config.json`. Users are responsible for securing access to their local machines. Do not share this configuration file, as it may contain API keys for optional AI integrations.

### Screen-Capture and Monitoring Risks
Ohverlay explicitly rejects silent employee monitoring. Any screen-capture feature (such as Blue Vision) requires explicit, manual user authorization per session or action.

### Credential Storage
Currently, third-party API keys (e.g., Anthropic, Groq) are stored in plaintext in the local configuration file. Users should use dedicated, scoped API keys for Ohverlay.

### Update and Package Verification
Future automated update mechanisms will require manifest verification (e.g., SHA-256 checksums). Do not install overlay packages from untrusted sources, as they consist of HTML/JS that runs within the local application context.
