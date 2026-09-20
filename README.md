# CivicAI

MCA project: AI-Based Urban Civic Complaint Classification and Prioritization System.

The MVP supports anonymous civic complaints with optional JPEG/PNG evidence and browser location, persisted through FastAPI in PostgreSQL. Accounts, video, maps, ML, classification and priority logic remain deferred; see [MVP scope](docs/MVP_SCOPE.md).

## Issue #3: photos and location

After pulling, install updated backend dependencies with `python -m pip install -e ".[test]"` using the project virtual environment, then run `python -m alembic upgrade head`. Restart both servers. Migration 0002 preserves existing complaints and adds nullable image_ref.

POST now uses multipart/form-data, including for text-only submissions. JSON clients must migrate; see docs/API_CONTRACT.md. The frontend handles this automatically.

Attach one optional JPEG/PNG (5 MiB maximum). Images must decode successfully and match their declared MIME, be at most 20 million pixels and have one frame. Re-encoding preserves orientation while removing EXIF/text metadata. Total multipart body is bounded to 5 MiB + 256 KiB. Stored filenames are generated, original names ignored, and image responses use explicit raster MIME plus nosniff. These measures reduce upload risks but do not replace production access controls or malware scanning.

Files are stored under data/uploads/complaints, excluded from Git, outside executable source paths. UPLOAD_DIR can override the directory; the backend needs write permission. PostgreSQL stores only relative image references. Back up files and database together. Ordinary persistence failures clean up newly saved files; process crashes may leave orphan files. Anonymous image URLs are suitable for local demonstration only.

Use “Use my current location” while near the issue. Permission is requested on demand; denial or timeout does not prevent submission. Browser location requires a secure context (HTTPS or trusted localhost) and device location availability. Location remains optional metadata and does not enter the current classification experiment.

Video, maps and manual coordinate entry are not offered. Avoid real private evidence in the demonstration database.

## Setup on Windows

Run from this repository folder in PowerShell. Use Python 3.12 and PostgreSQL (18 is installed on this computer). Dependencies are managed with standard pip and pyproject.toml; uv is not needed.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
Copy-Item .env.example .env
```

If the Python launcher is unavailable, use the full path to Python 3.12 instead of py -3.12. On this computer the bundled interpreter is:

```powershell
& 'C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
```

Use PostgreSQL's administration tools to create two empty databases: civicai and civicai_test. Give the test role permission to create schemas in civicai_test. Edit the ignored .env with your database URLs. Replace the placeholders; URL-encode special characters in credentials. Never share the password in chat. Environment variables take precedence over .env.

## Migrate and run

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m uvicorn civicai.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000/docs for the interactive API. Expand POST /api/v1/complaints, choose Try it out, enter a description and optional coordinates, and Execute. Copy the returned complaint_id into GET /api/v1/complaints/{complaint_id}; use GET /api/v1/complaints to see the list. GET /health reports process liveness without querying PostgreSQL.

Schema creation uses Alembic, never automatic startup table creation. All complaint endpoints are anonymous; use local demonstration data until access control is added.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

TEST_DATABASE_URL must point to a separate PostgreSQL database whose name ends in _test. Missing or unsafe configuration fails loudly. Tests create a uniquely named schema, apply the real Alembic migration, roll back each API test, and remove that schema at completion. No developer tables are truncated. A forcibly terminated test may leave its generated schema in the test database.

Health and database-unavailable tests need dependencies but no live PostgreSQL:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_api.py -k "health or unavailable"
```

Dependency ranges are in pyproject.toml; no resolved lock file is claimed yet. The current non-blocking dependency deprecation warnings are recorded in `docs/DEVELOPMENT_LOG.md`.

## Frontend setup and run

Use Node.js 22.12 or newer. In a second PowerShell window, while the backend is running on port 8000:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies API calls to the local FastAPI server, so no backend CORS change is required. A separately hosted frontend may set `VITE_API_BASE_URL` using `frontend/.env.example` as a guide.

Run the frontend tests and production build with:

```powershell
npm test
npm run build
```

Frontend dependencies are captured in `frontend/package-lock.json`.

### If the frontend reports 404 or “Queue unavailable”

First confirm that the backend is running at http://127.0.0.1:8000/health. Then stop the frontend development server with `Ctrl+C` and start it again from the `frontend` directory:

```powershell
npm run dev
```

The development proxy is loaded when Vite starts. Restarting is required after a stale development process or proxy-configuration change. A healthy proxy returns complaint JSON from http://127.0.0.1:5173/api/v1/complaints rather than the frontend HTML page.

## Files

- backend/src/civicai: schemas, routes, service logic, persistence, configuration.
- backend/migrations: Alembic environment and migration 0001.
- backend/tests: API, migration consistency and database constraint tests.
- frontend/src: React complaint form, recent-complaint list, API client, styles and interaction tests.
- docs: project context, [current state](docs/CURRENT_STATE.md), and [development log](docs/DEVELOPMENT_LOG.md).
- docs/reference/project-synopsis.docx: approved synopsis.
- ml, research and data: reserved for later milestones.

[Public repository](https://github.com/Soumodeep-Das/civic-ai). Earlier browser uploads created a separate GitHub history. Reconcile local/remote histories before pushing; no force push has been performed.
