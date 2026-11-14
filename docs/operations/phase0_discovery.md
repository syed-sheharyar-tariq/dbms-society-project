# Phase 0: Discovery, Architecture Summary & Risk Log

**Date**: 2026-11-14  
**Project**: Housing Society Complaint Management System (CMS)  
**Academic Setting**: Dawood University of Engineering and Technology (DBMS Course)  
**Target Organization**: Residential Housing Society (Gulistan-e-Jauhar, Karachi, Pakistan)  
**Scope**: ~800 houses/flats across 6 blocks (A, B, C, D, E, F)  

---

## 1. Technical Baseline & Host Environment

- **OS**: Windows 11
- **Python**: 3.11.18 (pinned via `.prototools`)
- **Node.js**: v26.13.0
- **npm**: 12.2.2
- **Git**: 2.56.1.windows.1 (monorepo initialized)
- **Containerization**: Docker not available on host; native virtualenv and Node environments selected for development, with standalone `Dockerfile.backend` prepared for remote deployment (Render / Railway / VPS).
- **Database & Auth**: Supabase PostgreSQL 15+ & Supabase Auth (Option A: Self-signup with office verification).
- **Storage**: Supabase Storage (`complaint-attachments` bucket).

---

## 2. Decision & Risk Log

| Item | Decision | Rationale |
| :--- | :--- | :--- |
| **Auth Strategy** | Option A (Self-signup + Office verification) | Matches actual housing society operational security: residents create auth accounts, but cannot view/file complaints until property occupancy is validated by society management. |
| **Incident-Complaint Model** | Dedicated association table `incident_complaint_links` | Prevents data loss when unlinking complaints, and uses partial unique index `WHERE unlinked_at IS NULL` to enforce at most one active link. |
| **Independent Confirmation** | Complaint moves to `pending_confirmation`, not `closed` | In accordance with PR-10, one resident's resolution approval cannot close another resident's complaint. |
| **Unverified Intake** | Disabled by default | Offline walk-ins or calls must match registered/verified properties to prevent phantom ticket spam. |
| **Overdue Logic** | Dynamic calculated query based on `expected_resolution_at` vs UTC now | Eliminates mutable drift and synchronization errors inherent to manual booleans. |
| **Cloud Hosting** | Vercel (frontend) + Render/Railway/VPS (backend) + Supabase (data) | Standard high-availability decoupled tiering recommended by the blueprint. |

---

## 3. Implementation Checklist & Phase Gates

- [x] **Phase 0: Discovery & Repository Scaffolding**
- [ ] **Phase 1: Database Architecture, Models & Migrations**
- [ ] **Phase 2: Auth, JWT, RBAC & Profiles**
- [ ] **Phase 3: Backend Foundation & API Core**
- [ ] **Phase 4: Complaint Workflows & Intake (AT-01 to AT-04)**
- [ ] **Phase 5: Incident Management & Grouping (AT-05 to AT-07)**
- [ ] **Phase 6: Routing & Dispatch (AT-08 to AT-13)**
- [ ] **Phase 7: Resolution & Resident Confirmation (AT-14 to AT-17)**
- [ ] **Phase 8: Frontend Foundation & Design System**
- [ ] **Phase 9: Role-Specific Frontend Portals**
- [ ] **Phase 10: Dashboards & Reporting Analytics (AT-24, AT-25)**
- [ ] **Phase 11: Hardening, Performance & Security Audit (AT-18 to AT-23)**
- [ ] **Phase 12: Deployment & CI/CD Pipeline (AT-26)**
- [ ] **Phase 13: Project Handover & Definition of Done Verification**
