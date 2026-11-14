# Housing Society Complaint Management System (CMS)

A production-grade, multi-role Complaint Management System designed for residential housing societies (~800 houses/flats across six residential blocks in Gulistan-e-Jauhar, Karachi, Pakistan).

**Academic Context**: Database Management Systems (DBMS), Dawood University of Engineering and Technology  
**Architecture**: Monorepo with React (Vite + TS + Tailwind) frontend, FastAPI (Python 3.11 + SQLAlchemy 2.0 + Alembic) backend, and PostgreSQL (Supabase Auth & Storage).

---

## Key Features & Invariants

1. **Independent Resident Confirmation (PR-10)**: Resolving an incident moves linked complaints to `pending_confirmation`. Each resident independently confirms or rejects resolution for their house/flat.
2. **Never Auto-Closes**: If a resident does not respond, the complaint remains in `pending_confirmation`.
3. **Decoupled Incidents & Complaints**: Many complaints group into one shared incident via `incident_complaint_links` with a partial unique constraint (`WHERE unlinked_at IS NULL`) ensuring at most one active link per complaint.
4. **Offline Multi-Channel Intake (PR-12)**: Complaint officers record phone, WhatsApp, and office-visit walk-in complaints with full attribution.
5. **Urgency & Escalation Flags (PR-09)**: Critical safety concerns (gas leaks, sparking electrical wires) are flagged urgent and highlighted in officer triage queues.
6. **Immutable Status & Audit History**: Append-only status transition history and operational audit logs for complete accountability.
7. **External Utility Case Tracking (PR-06, PR-07)**: Dedicated tracking for K-Electric, SSGC, and Water Board cases with chronological provider updates and response-time metrics.

---

## Repository Structure

```
d:\DBMS Project/
├── frontend/                  # React 18 + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── app/               # Router, providers, Supabase Auth state
│   │   ├── api/               # Centralized Axios client & typed endpoints
│   │   ├── components/        # Reusable UI primitives (dialogs, tables, badges)
│   │   └── features/          # Role portals (resident, officer, staff, admin)
│   └── package.json
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── core/              # Config, security, JWT verification, errors
│   │   ├── api/v1/            # Versioned API routes
│   │   ├── models/            # SQLAlchemy 2.0 relational models
│   │   ├── schemas/           # Pydantic v2 validation models
│   │   ├── repositories/      # Optimized database query repositories
│   │   ├── services/          # Business workflows & state transitions
│   │   └── main.py            # FastAPI entry point
│   ├── alembic/               # Database migration scripts
│   ├── tests/                 # Unit, integration, security & regression tests
│   └── requirements.txt
├── database/
│   └── seed/                  # Idempotent seed scripts (blocks, categories, utilities)
├── docs/                      # Architectural specs, ERD, API contracts, operations
├── infra/                     # Dockerfile, render.yaml, vercel.json configurations
├── .env.example               # Environment variables template
├── .gitignore
└── README.md
```

---

## Getting Started

### 1. Environment Setup
Copy the configuration template:
```bash
cp .env.example .env
```
Fill in your Supabase project credentials (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `DATABASE_URL`, etc.).

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m app.core.bootstrap_admin --help
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Acceptance Criteria & Test Matrix
This project satisfies all 26 mandatory acceptance tests (AT-01 through AT-26) defined in the Master AI Blueprint.
