# Ohverlay Enterprise Plan for Sarh Attaqnia

## Purpose

This document defines the next product direction for **Ohverlay** as an internal company workflow platform, with **Sarh Attaqnia** as the first client tenant.

The immediate use case is network-based file handoff with traceability. The longer-term product is a modular company desktop platform with:

- file handoff and routing
- private messaging
- company AI with RAG
- employee directory and roles
- supervisor analytics and audit trails
- multi-tenant packaging for future companies

## Product Direction

Ohverlay should evolve into a **desktop-first company operations layer**.

The desktop app remains the daily user surface:

- glowing overlays
- semi-transparent post-it interactions
- tray controls
- quick composer panels
- per-user local logs and cache

The backend becomes the company brain:

- employee directory
- permissions and roles
- message and handoff history
- knowledge base and retrieval
- analytics and monitoring
- tenant configuration

## Operating Modes

### Mode 1: Local Network Mode

This is the current fastest path for Sarh Attaqnia.

- each employee has a shared folder
- only the folder owner has write access
- Ohverlay writes small metadata JSON files into `_ohverlay/`
- recipients poll peer folders
- local machine stores audit logs

This mode is good for:

- pilot rollout
- proving the workflow
- getting IT trust
- operating without a server in phase 1

### Mode 2: Managed Company Mode

This is the medium-term platform mode.

- desktop app authenticates against a central company backend
- handoffs, messages, analytics, and AI retrieval use central services
- local client still caches activity for resilience and offline support

This mode is required for:

- private messaging
- multi-recipient delivery state
- supervisor dashboards
- employee/role directory
- company AI with project and policy retrieval
- app-market multi-tenancy

## Target User Flows

### File Handoff Flow

1. Creator selects a file or folder in Ohverlay.
2. Creator chooses one or more recipients from a dropdown or search list.
3. Creator adds an optional message.
4. Ohverlay writes a structured handoff event.
5. Recipient sees a glowing post-it overlay with sender, file info, and action button.
6. Recipient hovers or clicks the overlay.
7. Ohverlay opens the exact file path or parent folder.
8. The client logs `delivered`, `opened`, and `acknowledged` events locally.
9. Supervisors can later review a trace of the interaction.

### Coordinator Source-Of-Truth Flow

This is the practical next step for drawing issuances, final plans, and other
reference files that should come from one controlled owner.

1. A coordinator owns a common reference folder on the network.
2. The coordinator can add or replace files in that folder.
3. Other users can read from the folder, but cannot delete controlled files.
4. Ohverlay dispatches a handoff or announcement pointing to the reference item.
5. Recipients open the routed item from the overlay or activity console.
6. The system logs who was notified and who opened the reference path.

Important limitation for the current local-network phase:

- Ohverlay can reliably log `sent`, `received`, and `opened`.
- It cannot reliably prove that a user copied a file after opening it without
  deeper filesystem auditing or a central service.
- If copy tracking becomes mandatory, that should move into the managed backend
  phase with stronger audit controls.

### Private Messaging Flow

1. User opens a message thread with a coworker or team.
2. Message appears as a lightweight overlay and in the message center.
3. Read receipt and acknowledgement are logged.
4. Retention and visibility follow company policy.

### Company AI Flow

1. User asks a question inside Ohverlay.
2. AI retrieves only documents allowed for that employee role and tenant.
3. AI answers with citations to project files, policies, or employee references.
4. Conversation is logged according to company retention policy.

## Architecture Principles

- **Desktop-first**: the overlay experience is the product surface.
- **Local-first where possible**: local cache, local logs, and offline-safe behavior.
- **Centralize only what must be shared**: identity, permissions, analytics, messaging, AI knowledge.
- **Tenant isolation by design**: Sarh Attaqnia data must never mix with future tenants.
- **Role-aware AI**: answers must be filtered by employee permissions.
- **Observable interactions**: important events become auditable records.
- **Policy transparency**: monitoring must be explicit and documented to staff.

## Recommended Technical Stack

### Desktop Client

- Python
- PySide6
- SQLite for local cache and local audit queue
- JSON config for simple user settings

### Backend

- FastAPI
- PostgreSQL
- Redis for transient queues and notifications
- object storage for uploaded documents and attachments
- vector store using PostgreSQL `pgvector` or a dedicated vector DB later

### AI Layer

- ingestion workers for document parsing and chunking
- embeddings pipeline
- role-filtered retrieval
- answer generation with source citations

## Recommended Repo Direction

The current repo already has a workable desktop structure:

- `main.py`
- `engine/`
- `modules/`
- `ui/`
- `utils/`

The next step is to formalize it into a modular platform layout without breaking the current app.

```text
ohverlay/
  main.py
  engine/
    app_runtime.py
    event_bus.py
    module_registry.py
    sync_manager.py
    tenant_context.py
  modules/
    file_handoff/
      service.py
      local_transport.py
      server_transport.py
      models.py
      audit.py
    messaging/
      service.py
      models.py
      notifications.py
    directory/
      service.py
      models.py
    ai_assistant/
      service.py
      retrieval.py
      policies.py
    supervisor/
      analytics.py
      exports.py
  ui/
    overlays/
      handoff_card.py
      message_card.py
      ai_card.py
    composer/
      handoff_composer.py
      message_composer.py
    console/
      activity_console.py
      supervisor_console.py
    tray/
      menu.py
  backend/
    app/
      api/
        routes_auth.py
        routes_handoffs.py
        routes_messages.py
        routes_ai.py
        routes_admin.py
      services/
        auth_service.py
        handoff_service.py
        messaging_service.py
        retrieval_service.py
        analytics_service.py
      models/
        tenant.py
        employee.py
        role.py
        handoff.py
        message.py
        document.py
        audit_event.py
      db/
        base.py
        session.py
    migrations/
  tests/
    desktop/
    backend/
    integration/
  docs/
    sarh_attaqnia_ohverlay_enterprise_plan.md
```

## Module Boundaries

### Desktop Core

Responsible for:

- startup
- tray lifecycle
- overlay orchestration
- local event queue
- sync jobs
- tenant/user session

Should not own:

- business rules for handoffs
- messaging rules
- RAG retrieval logic

### File Handoff Module

Responsible for:

- composer UI
- recipient selection
- file and folder routing
- delivery state
- local audit emission
- server sync when available

Should support two transports:

- `local_transport`: current shared-folder JSON mode
- `server_transport`: future backend mode

### Messaging Module

Responsible for:

- direct messages
- thread state
- receipts
- overlay notifications

### Directory Module

Responsible for:

- employee list
- teams
- roles
- supervisor mappings

### AI Assistant Module

Responsible for:

- AI chat panel
- retrieval requests
- citations
- role-aware filters

### Supervisor Module

Responsible for:

- event summaries
- response-time views
- exports
- inventory/audit reports

## Data Model

### Core Tenant Tables

#### `tenants`

- `id`
- `slug`
- `display_name`
- `status`
- `created_at`

#### `tenant_settings`

- `id`
- `tenant_id`
- `branding_json`
- `feature_flags_json`
- `retention_policy_json`
- `created_at`
- `updated_at`

### People and Access Tables

#### `employees`

- `id`
- `tenant_id`
- `employee_code`
- `full_name`
- `email`
- `department`
- `job_title`
- `status`
- `created_at`

#### `roles`

- `id`
- `tenant_id`
- `name`
- `description`

#### `employee_roles`

- `id`
- `employee_id`
- `role_id`

#### `devices`

- `id`
- `tenant_id`
- `employee_id`
- `hostname`
- `os_name`
- `client_version`
- `last_seen_at`

### File Handoff Tables

#### `shared_locations`

- `id`
- `tenant_id`
- `employee_id`
- `location_type`
- `path`
- `is_active`

#### `file_handoffs`

- `id`
- `tenant_id`
- `creator_employee_id`
- `source_location_id`
- `file_name`
- `file_path`
- `file_hash`
- `message`
- `priority`
- `created_at`

#### `file_handoff_targets`

- `id`
- `handoff_id`
- `target_employee_id`
- `delivery_status`
- `delivered_at`
- `opened_at`
- `acknowledged_at`

#### `handoff_events`

- `id`
- `tenant_id`
- `handoff_id`
- `target_employee_id`
- `event_type`
- `event_time`
- `device_id`
- `event_payload_json`

### Messaging Tables

#### `message_threads`

- `id`
- `tenant_id`
- `thread_type`
- `created_by_employee_id`
- `created_at`

#### `thread_participants`

- `id`
- `thread_id`
- `employee_id`
- `role_in_thread`

#### `messages`

- `id`
- `tenant_id`
- `thread_id`
- `sender_employee_id`
- `body`
- `attachment_json`
- `created_at`

#### `message_receipts`

- `id`
- `message_id`
- `employee_id`
- `delivered_at`
- `read_at`

### AI and Knowledge Tables

#### `knowledge_sources`

- `id`
- `tenant_id`
- `source_type`
- `display_name`
- `path_or_uri`
- `visibility_policy_json`
- `last_ingested_at`

#### `documents`

- `id`
- `tenant_id`
- `knowledge_source_id`
- `title`
- `document_type`
- `checksum`
- `storage_uri`
- `created_at`

#### `document_chunks`

- `id`
- `document_id`
- `chunk_index`
- `chunk_text`
- `embedding_vector`
- `visibility_policy_json`

#### `ai_threads`

- `id`
- `tenant_id`
- `employee_id`
- `created_at`

#### `ai_messages`

- `id`
- `ai_thread_id`
- `sender_type`
- `body`
- `sources_json`
- `created_at`

### Audit Table

#### `audit_events`

- `id`
- `tenant_id`
- `employee_id`
- `device_id`
- `event_type`
- `entity_type`
- `entity_id`
- `payload_json`
- `created_at`

## Event Taxonomy

Standardizing events early will make analytics and supervisor reports simple later.

Recommended event names:

- `handoff_created`
- `handoff_delivery_detected`
- `handoff_overlay_shown`
- `handoff_overlay_opened`
- `handoff_path_opened`
- `handoff_ack_written`
- `handoff_ack_received`
- `message_sent`
- `message_delivered`
- `message_read`
- `ai_query_submitted`
- `ai_answer_returned`
- `ai_source_clicked`
- `supervisor_report_exported`

## Local Client Storage

Move from JSONL-only logging into a small local SQLite database.

Recommended local files:

- `%USERPROFILE%\\.ohverlay\\config.json`
- `%USERPROFILE%\\.ohverlay\\client.db`
- `%USERPROFILE%\\.ohverlay\\logs\\ohverlay.log`

The local DB should store:

- pending sync events
- recent handoffs
- recent messages
- overlay state
- local analytics cache

## RAG Design for Company AI

The AI must be **tenant-scoped** and **role-filtered**.

Allowed sources for Sarh Attaqnia may include:

- project folders
- contracts
- SOPs
- policies
- org charts
- employee directory metadata
- coordinator notes

Rules:

- retrieval must respect tenant boundaries
- retrieval must respect employee role visibility
- answers should cite sources
- unsupported answers should say they are uncertain
- sensitive HR or executive data should require explicit role grants

## Supervisor and Monitoring Design

Monitoring should be designed as **transparent operational auditing**, not hidden surveillance.

Recommended supervisor views:

- handoffs by employee
- handoffs by department
- response time by recipient
- unopened handoffs
- daily activity summary
- message volume summary
- AI query volume by team

Recommended export types:

- CSV
- JSON
- daily emailed report later

## IT Approval Checklist for Sarh Attaqnia

This is the minimum permission list to request from top managers and IT.

### For Phase 1

- approve per-user installation of `Ohverlay.exe`
- approve creation of `_ohverlay/` metadata folders inside employee share paths
- confirm read access between intended peer folders
- confirm each employee keeps write access only to their own shared folder
- approve local logs in the user profile directory
- approve pilot users and departments

### For Phase 2 and Beyond

- provide a Windows or Linux VM for internal API hosting
- approve PostgreSQL database hosting
- approve internal DNS name for the Ohverlay API
- approve firewall access for desktop clients to internal API
- approve service account access for document ingestion
- approve data retention and monitoring policy
- approve role mapping source such as HR export or directory service

## Recommended Delivery Phases

### Phase 1: Sarh Attaqnia File Handoff Pilot

Goal:

- deliver the workflow already envisioned by users

Scope:

- sender overlay composer
- file or folder picker
- dropdown or searchable recipient list
- optional multi-recipient support
- glowing recipient overlay
- click-to-open exact path
- local audit log and mini activity console
- coordinator-owned source-of-truth folder pattern for controlled references

Acceptance criteria:

- creator can send to at least one recipient from the overlay
- recipient can open the file path from the glowing card
- sender, recipient, time, and file info are all logged
- supervisor can review a basic local activity export

### Phase 1.5: Controlled Reference Cleanup

Goal:

- keep shared reference folders healthy without losing accountability

Scope:

- weekly diagnostics for stale or duplicate reference files
- candidate cleanup list for the coordinator
- creator confirmation prompt before deletion
- one-click cleanup action with audit logging

Note:

- destructive cleanup should only be enabled after the reference-folder model
  is stable and user permissions are clearly defined.

### Phase 2: Central Audit and Directory

Goal:

- move from local-only logs to company-visible reporting

Scope:

- FastAPI backend
- PostgreSQL
- employee directory
- role model
- sync local events to server
- supervisor dashboard

### Phase 3: Private Messaging

Goal:

- introduce lightweight internal communication inside Ohverlay

Scope:

- one-to-one messaging
- thread history
- read receipts
- message overlays

### Phase 4: Company AI for Sarh Attaqnia

Goal:

- provide an internal AI assistant backed by company documents

Scope:

- document ingestion pipeline
- tenant-scoped vector retrieval
- policy-aware citations
- project and employee lookup

### Phase 5: Multi-Tenant Productization

Goal:

- prepare Ohverlay for other companies and app-market distribution

Scope:

- tenant branding
- feature flags
- deployment templates
- tenant provisioning flow
- marketplace packaging

## Immediate Implementation Recommendation

Build **Phase 1** first inside the current desktop app.

The next concrete engineering tasks should be:

1. Add a sender-side handoff composer overlay.
2. Add structured handoff models instead of loose JSON blobs.
3. Add exact path opening, not just folder opening.
4. Replace JSONL-only audit with local SQLite plus export.
5. Add a simple supervisor report view or export screen.

That gets Sarh Attaqnia a working internal pilot without waiting for backend approval.

## Product Positioning

For Sarh Attaqnia, Ohverlay becomes:

- an internal handoff tracker
- a communication layer
- a company memory surface
- a supervisor analytics tool
- later, a tenant-ready enterprise desktop platform

This keeps the visual identity of Ohverlay while turning it into a serious operations product.

## Adjacent Modules To Add Soon

### Desktop Post-It Notes

These should become a separate overlay module, not mixed into file handoff cards.

Recommended capabilities:

- user-created sticky notes anywhere on screen
- color-coded note themes
- adjustable size
- adjustable transparency
- optional countdown or elapsed timer
- pin, archive, and close actions
- local persistence across restarts

### Group Announcements

Administrators should be able to send branded full-team overlays for:

- policy changes
- shift notices
- emergency announcements
- milestone updates

### Company AI Oracle

The long-term assistant should support:

- project-aware retrieval
- policy retrieval
- employee and role directory lookup
- IT-oriented server health summaries
- administrator broadcast drafting
- future sub-agent orchestration only after backend permissions and audit are in place
