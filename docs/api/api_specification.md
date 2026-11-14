# Housing Society CMS - REST API Contract

**Base URL**: `/api/v1`  
**Interactive Docs**: `/docs` (Swagger UI) & `/redoc` (ReDoc)  
**Standard Response Format**: JSON with UTC ISO-8601 timestamps.

---

## 1. Authentication & Session

- `GET /api/v1/me`: Returns profile of authenticated caller and verified property associations (if resident).
- `PATCH /api/v1/me`: Updates editable profile information (name, phone).

---

## 2. Master Data

- `GET /api/v1/blocks`: List society blocks (A through F).
- `GET /api/v1/properties`: List houses and flats (supports `?block_id=UUID`).
- `GET /api/v1/categories`: List complaint categories (Electricity, Water, Gas, Sewerage, Streetlights).

---

## 3. Complaints

- `POST /api/v1/complaints`: Resident creates complaint for authorized property. Supports `Idempotency-Key` header.
- `POST /api/v1/complaints/offline`: Complaint officer registers walk-in, phone, or WhatsApp complaint (PR-12).
- `GET /api/v1/complaints`: Paginated list of complaints (scoped to resident if resident; filterable by status, block, category, urgency).
- `GET /api/v1/complaints/{id}`: Detailed view including status history timeline and active incident progress.
- `POST /api/v1/complaints/{id}/confirmations`: Resident resolution feedback (`outcome: 'confirmed'` -> closed, or `'rejected'` -> reopened).

---

## 4. Incidents & Grouping

- `POST /api/v1/incidents`: Group multiple complaints into a shared operational incident.
- `GET /api/v1/incidents`: Paginated list of incidents.
- `GET /api/v1/incidents/{id}`: Incident details with linked complaints and assignments.
- `PATCH /api/v1/incidents/{id}/status`: Transition incident status. Marking `resolved` moves all eligible complaints to `pending_confirmation`.
- `POST /api/v1/incidents/{id}/links`: Link an additional complaint.
- `DELETE /api/v1/incidents/{id}/links/{link_id}`: Unlink complaint with mandatory reason.

---

## 5. Work Assignments

- `POST /api/v1/incidents/{id}/assignments`: Assign active field staff member to an incident.
- `GET /api/v1/assignments`: List work assignments (field staff only see their own assignments).
- `PATCH /api/v1/assignments/{id}`: Update assignment status (`accepted`, `in_progress`, `blocked`, `completed`). Mandatory notes for completion.

---

## 6. External Utilities

- `GET /api/v1/utilities/companies`: Directory of utility providers (K-Electric, SSGC, Water Board).
- `POST /api/v1/incidents/{id}/utility-cases`: Lodge external tracking ticket with provider reference and expected due date.
- `GET /api/v1/utility-cases`: List utility cases with dynamic overdue calculation.
- `POST /api/v1/utility-cases/{id}/updates`: Log timestamped provider replies or society follow-ups.

---

## 7. Reporting & Admin

- `GET /api/v1/dashboard/summary`: Top-level operational KPIs.
- `GET /api/v1/reports/recurring-faults`: Recurring incident clusters by block/area (default 90 days).
- `GET /api/v1/reports/staff-workload`: Staff workload by assignment state.
- `GET /api/v1/reports/utility-response-times`: Utility first-response latency and resolution time.
- `GET /api/v1/admin/users`: List profiles and manage roles (admin only).
- `POST /api/v1/admin/residents/{id}/verify`: Verify resident property occupancy.
- `POST /api/v1/admin/property-residents`: Create property-resident association.
- `GET /api/v1/admin/audit-logs`: Immutable audit log trail.
- `POST /api/v1/attachments`: Supabase storage metadata upload.
