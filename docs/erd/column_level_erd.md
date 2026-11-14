# Column-Level Data Dictionary & Relational Schema

**Project**: Housing Society Complaint Management System (Gulistan-e-Jauhar, Karachi)  
**Academic Context**: DBMS Course, Dawood University of Engineering and Technology  
**Database**: PostgreSQL 15+ (Hosted on Supabase)

---

## 1. Relational ERD (Mermaid)

```mermaid
erDiagram
    BLOCKS {
        uuid id PK
        varchar(20) code UK
        varchar(100) name UK
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    PROPERTIES {
        uuid id PK
        uuid block_id FK
        varchar(40) property_number
        varchar(20) property_type
        text address_note
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    PROFILES {
        uuid id PK
        uuid auth_user_id UK
        varchar(30) role
        varchar(150) full_name
        varchar(30) phone
        varchar(254) email
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    RESIDENTS {
        uuid id PK
        uuid profile_id FK,UK
        varchar(20) verification_status
        uuid verified_by FK
        timestamptz verified_at
        timestamptz created_at
        timestamptz updated_at
    }

    PROPERTY_RESIDENTS {
        uuid id PK
        uuid property_id FK
        uuid resident_id FK
        varchar(30) relationship_type
        date valid_from
        date valid_until
        boolean is_primary_contact
        timestamptz created_at
    }

    CATEGORIES {
        uuid id PK
        varchar(80) name UK
        text description
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    UTILITY_COMPANIES {
        uuid id PK
        varchar(150) name UK
        text contact_info
        varchar(30) contact_phone
        varchar(254) contact_email
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    COMPLAINTS {
        uuid id PK
        varchar(30) complaint_number UK
        uuid resident_id FK
        uuid property_id FK
        uuid category_id FK
        text description
        varchar(30) status
        boolean is_urgent
        text urgency_reason
        varchar(20) intake_channel
        uuid recorded_by_profile_id FK
        timestamptz submitted_at
        timestamptz resolved_reported_at
        timestamptz closed_at
        timestamptz updated_at
    }

    INCIDENTS {
        uuid id PK
        varchar(30) incident_number UK
        uuid category_id FK
        varchar(180) title
        text description
        varchar(30) status
        varchar(20) routing_type
        varchar(20) priority
        text area_description
        uuid created_by FK
        timestamptz created_at
        timestamptz resolved_at
        timestamptz closed_at
        timestamptz updated_at
    }

    INCIDENT_COMPLAINT_LINKS {
        uuid id PK
        uuid incident_id FK
        uuid complaint_id FK
        uuid linked_by FK
        timestamptz linked_at
        uuid unlinked_by FK
        timestamptz unlinked_at
        text unlink_reason
    }

    WORK_ASSIGNMENTS {
        uuid id PK
        uuid incident_id FK
        uuid staff_profile_id FK
        uuid assigned_by_profile_id FK
        varchar(20) status
        timestamptz assigned_at
        timestamptz accepted_at
        timestamptz started_at
        timestamptz completed_at
        text completion_notes
        timestamptz ended_at
        timestamptz created_at
        timestamptz updated_at
    }

    ASSIGNMENT_UPDATES {
        uuid id PK
        uuid assignment_id FK
        uuid actor_profile_id FK
        varchar(40) update_type
        text message
        varchar(20) old_status
        varchar(20) new_status
        timestamptz created_at
    }

    UTILITY_CASES {
        uuid id PK
        uuid incident_id FK
        uuid utility_company_id FK
        varchar(100) external_reference_number
        varchar(20) status
        timestamptz submitted_at
        timestamptz expected_resolution_at
        timestamptz first_response_at
        timestamptz resolved_at
        uuid created_by FK
        timestamptz created_at
        timestamptz updated_at
    }

    UTILITY_CASE_UPDATES {
        uuid id PK
        uuid utility_case_id FK
        uuid actor_profile_id FK
        varchar(20) direction
        varchar(40) update_type
        text message
        timestamptz provider_event_at
        timestamptz recorded_at
        varchar(500) attachment_path
    }

    COMPLAINT_STATUS_HISTORY {
        uuid id PK
        uuid complaint_id FK
        varchar(30) old_status
        varchar(30) new_status
        uuid changed_by_profile_id FK
        text reason
        timestamptz changed_at
    }

    INCIDENT_STATUS_HISTORY {
        uuid id PK
        uuid incident_id FK
        varchar(30) old_status
        varchar(30) new_status
        uuid changed_by_profile_id FK
        text reason
        timestamptz changed_at
    }

    RESOLUTION_CONFIRMATIONS {
        uuid id PK
        uuid complaint_id FK
        uuid resident_id FK
        int cycle_number
        varchar(20) outcome
        text feedback
        timestamptz responded_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid actor_profile_id FK
        varchar(60) action
        varchar(50) entity_type
        uuid entity_id
        varchar(64) request_id
        jsonb old_values
        jsonb new_values
        timestamptz created_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid recipient_profile_id FK
        varchar(50) type
        varchar(150) title
        text body
        varchar(50) target_type
        uuid target_id
        timestamptz created_at
        timestamptz read_at
    }

    ATTACHMENTS {
        uuid id PK
        varchar(40) entity_type
        uuid entity_id
        uuid uploader_profile_id FK
        varchar(255) file_name
        varchar(500) storage_path
        varchar(100) mime_type
        int file_size_bytes
        timestamptz created_at
    }

    BLOCKS ||--o{ PROPERTIES : contains
    PROFILES ||--o| RESIDENTS : identifies
    RESIDENTS ||--o{ PROPERTY_RESIDENTS : occupies
    PROPERTIES ||--o{ PROPERTY_RESIDENTS : has
    RESIDENTS ||--o{ COMPLAINTS : submits
    PROPERTIES ||--o{ COMPLAINTS : concerns
    CATEGORIES ||--o{ COMPLAINTS : classifies
    INCIDENTS ||--o{ INCIDENT_COMPLAINT_LINKS : groups
    COMPLAINTS ||--o{ INCIDENT_COMPLAINT_LINKS : linked
    INCIDENTS ||--o{ WORK_ASSIGNMENTS : receives
    PROFILES ||--o{ WORK_ASSIGNMENTS : assigned
    INCIDENTS ||--o{ UTILITY_CASES : routes
    UTILITY_COMPANIES ||--o{ UTILITY_CASES : handles
    UTILITY_CASES ||--o{ UTILITY_CASE_UPDATES : receives
    WORK_ASSIGNMENTS ||--o{ ASSIGNMENT_UPDATES : logs
    COMPLAINTS ||--o{ COMPLAINT_STATUS_HISTORY : records
    INCIDENTS ||--o{ INCIDENT_STATUS_HISTORY : records
    COMPLAINTS ||--o{ RESOLUTION_CONFIRMATIONS : receives
    PROFILES ||--o{ AUDIT_LOGS : performs
```

---

## 2. Integrity Constraints & Invariants

1. **`uq_properties_block_number`**: `UNIQUE(block_id, property_number)` ensures unique property addresses within a block.
2. **`uq_active_incident_link_per_complaint`**: Partial unique index on `incident_complaint_links (complaint_id) WHERE unlinked_at IS NULL`. Guarantees a complaint can belong to at most one open incident, while retaining historic links.
3. **`uq_utility_case_provider_reference`**: Partial unique index on `utility_cases (utility_company_id, external_reference_number) WHERE external_reference_number IS NOT NULL`. Prevents duplicate tracking references per provider.
4. **`uq_resolution_confirmations_complaint_cycle`**: `UNIQUE(complaint_id, cycle_number)` enforces independent feedback per resolution attempt.
5. **No Cascading Hard Deletes**: Foreign keys default to `ON DELETE RESTRICT` (and `SET NULL` for actor audit contexts) to preserve historical integrity.
