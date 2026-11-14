# Housing Society CMS - Operations & Administration Guide

**Operational Setting**: Gulistan-e-Jauhar, Karachi, Pakistan  
**Academic Context**: DBMS Course, Dawood University of Engineering and Technology  

---

## 1. Initial Administrator Bootstrap

To prevent privilege escalation, public signup never grants `administrator`, `complaint_officer`, or `field_staff` roles.
To initialize the first society administrator:

1. Create a user account in your Supabase Auth dashboard (or register via the app).
2. Note the created Supabase Auth UUID (Subject).
3. Execute the secure CLI bootstrap command from the `backend/` directory:
   ```bash
   python -m app.core.bootstrap_admin --auth-user-id "<SUPABASE_AUTH_UUID>" --full-name "Chief Society Administrator" --email "admin@jauhar.com" --phone "+92-300-1234567"
   ```
4. The script creates the profile with `role='administrator'` and commits an immutable event to `audit_logs`.
5. Rerunning this command will safely refuse to overwrite an existing administrator.

---

## 2. Database Migrations & Seeding

### Applying Alembic Migrations
```bash
cd backend
alembic upgrade head
```

### Seeding Master Data (Blocks, Categories, Utilities)
The seed script is idempotent and safe to run multiple times:
```bash
cd backend
python -m app.database_seed
```
Seeds:
- **Blocks**: BLK-A through BLK-F (Block A to Block F).
- **Categories**: Electricity, Water, Gas, Sewerage, Streetlights.
- **Utility Companies**: K-Electric (118), SSGC (1199), Karachi Water & Sewerage Corporation (99245138).

---

## 3. Disaster Recovery & Backups

1. **Automated Supabase Backups**: Managed daily point-in-time recovery (PITR) enabled via Supabase dashboard.
2. **Manual Logical Backup (pg_dump)**:
   ```bash
   pg_dump --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" -F c -f society_cms_backup.dump
   ```
3. **Restore Rehearsal**:
   ```bash
   pg_restore --clean --if-exists -d "$TEST_DATABASE_URL" society_cms_backup.dump
   ```

---

## 4. Cloud Deployment Runbooks

### Vercel (Frontend SPA)
1. Import repository on Vercel.
2. Root directory is handled automatically via `vercel.json`.
3. Set Environment Variables:
   - `VITE_API_BASE_URL`: URL of your deployed FastAPI backend (e.g., `https://cms-api.onrender.com/api/v1`)
   - `VITE_SUPABASE_URL`: `https://your-project.supabase.co`
   - `VITE_SUPABASE_ANON_KEY`: Your Supabase public anonymous key.

### Netlify (Frontend Alternative)
1. Import repository on Netlify.
2. Configuration loaded automatically via `netlify.toml`.
3. Configure identical `VITE_` variables in Site Settings.

### Render / Railway (FastAPI Backend)
1. Connect GitHub repo to Render as a Web Service (or via `render.yaml`).
2. Build Command: `pip install -r backend/requirements.txt`
3. Start Command: `cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables from `.env.example`.
5. Ensure `CORS_ORIGINS` includes your production frontend URL (e.g., `https://society-cms.vercel.app`).
