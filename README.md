# CivicAI

MCA project: AI-Based Urban Civic Complaint Classification and Prioritization System.

The MVP supports anonymous civic complaints persisted through FastAPI in PostgreSQL. Issue #4 adds an accessible issue-location picker and requires a photo plus a confirmed issue location in the citizen frontend. The backend keeps both fields nullable so existing records and direct API clients remain compatible. Accounts, video, ML, classification and priority logic remain deferred; see [MVP scope](docs/MVP_SCOPE.md).

## Issue #4: accessible issue-location selection

Citizens can explicitly search by locality, PIN code, street, address or landmark, use their current device position, and optionally refine the selected point on a map. Search results can be selected and confirmed without operating the map. The form identifies the selected location as exact, approximate or broad and requires confirmation after any map adjustment.

The frontend requires one valid JPEG/PNG photo and one confirmed location before submitting. This is a user-experience rule for the citizen form, not a breaking backend constraint: old location-free records and trusted direct API clients remain supported. A selected location describes the civic issue, not necessarily the reporter's current position. Nearby details should help municipal staff identify the site but must not contain private personal information.

Search is sent only when the user presses Search or Enter; there is no type-ahead traffic. The local-demo adapter is compatible with public Nominatim and applies one-request-per-second pacing plus a short bounded cache. Public Nominatim and the default MapLibre demonstration style provide no production availability guarantee. Configure or replace both providers before public deployment; see `frontend/.env.example`, `.env.example` and `docs/ISSUE_004_LOCATION_SELECTION.md`.

## Issue #3: photos and location

After pulling, install updated backend dependencies with `python -m pip install -e ".[test]"` using the project virtual environment, then run `python -m alembic upgrade head`. Restart both servers. Migrations 0002 and 0003 preserve existing complaints while adding nullable image and location-context fields.

POST now uses multipart/form-data, including for text-only submissions. JSON clients must migrate; see docs/API_CONTRACT.md. The frontend handles this automatically.

Attach one optional JPEG/PNG (5 MiB maximum). Images must decode successfully and match their declared MIME, be at most 20 million pixels and have one frame. Re-encoding preserves orientation while removing EXIF/text metadata. Total multipart body is bounded to 5 MiB + 256 KiB. Stored filenames are generated, original names ignored, and image responses use explicit raster MIME plus nosniff. These measures reduce upload risks but do not replace production access controls or malware scanning.

Files are stored under data/uploads/complaints, excluded from Git, outside executable source paths. UPLOAD_DIR can override the directory; the backend needs write permission. PostgreSQL stores only relative image references. Back up files and database together. Ordinary persistence failures clean up newly saved files; process crashes may leave orphan files. Anonymous image URLs are suitable for local demonstration only.

Use “Use my current location” while near the issue. Permission is requested on demand; denial or timeout does not prevent submission. The browser may use a device fix from the last five minutes and waits up to 30 seconds for one. Browser location requires a secure context (HTTPS or trusted localhost), operating-system Location Services and an available location provider; on Windows, keep Location Services and Wi-Fi enabled. Location remains optional metadata and does not enter the current classification experiment.

Video and manual coordinate entry are not offered. Issue #4 provides an optional map for refining a searched or device-derived location. Avoid real private evidence in the demonstration database.

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

Use PostgreSQL's administration tools to create two empty databases: civicai and civicai_test. Give the test role permission to create schemas in civicai_test. Edit the ignored .env with your database URLs and geocoder configuration. Replace the placeholders; URL-encode special characters in credentials. Never share the password in chat. Environment variables take precedence over .env.

## Migrate and run

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m uvicorn civicai.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000/docs for the interactive API. Expand POST /api/v1/complaints, choose Try it out, enter a description and optional coordinates, and Execute. Copy the returned complaint_id into GET /api/v1/complaints/{complaint_id}; use GET /api/v1/complaints to see the list. GET /health reports process liveness without querying PostgreSQL.

Schema creation uses Alembic, never automatic startup table creation. All complaint endpoints are anonymous; use local demonstration data until access control is added.

### Start the complete local MVP with one command

After completing the backend and frontend setup once, run this from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

The helper checks the backend and frontend first, starts only the service that is missing, waits for both ports, and verifies that the Vite API proxy returns JSON. Services are started as hidden local processes so closing this PowerShell window does not immediately stop the site. Runtime output is written to the ignored `logs` directory. Re-run the same command whenever http://127.0.0.1:5173 cannot be reached.

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

`VITE_MAP_STYLE_URL` selects the MapLibre style and defaults to MapLibre's public demonstration style. The map code is loaded only when a user opens the optional map. On this computer the global `npm` wrapper may fail because its roaming `npm-cli.js` is missing; the repository-local commands used for verification were `node .\node_modules\vitest\vitest.mjs run`, `node .\node_modules\typescript\bin\tsc -b`, and `node .\node_modules\vite\bin\vite.js build`.

### If the frontend reports 404 or “Queue unavailable”

Run the repository startup helper first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

For a frontend that is already running but serving a stale proxy configuration, stop that frontend process and start it again from the `frontend` directory:

```powershell
npm run dev
```

The development proxy is loaded when Vite starts. Restarting is required after a stale development process or proxy-configuration change. A healthy proxy returns complaint JSON from http://127.0.0.1:5173/api/v1/complaints rather than the frontend HTML page.

## Files

- backend/src/civicai: schemas, routes, service logic, persistence, configuration.
- backend/migrations: Alembic environment and migrations through 0003.
- backend/tests: API, migration consistency and database constraint tests.
- frontend/src: React complaint form, accessible location picker, lazy-loaded map, recent-complaint list, API client, styles and interaction tests.
- scripts/start-dev.ps1: checks and starts both local development services, then verifies the API proxy.
- docs: project context, [current state](docs/CURRENT_STATE.md), and [development log](docs/DEVELOPMENT_LOG.md).
- docs/reference/project-synopsis.docx: approved synopsis.
- ml, research and data: reserved for later milestones.

[Public repository](https://github.com/Soumodeep-Das/civic-ai). Earlier browser uploads created a separate GitHub history. Reconcile local/remote histories before pushing; no force push has been performed.
