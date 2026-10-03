# CivicAI

MCA project: AI-Based Urban Civic Complaint Classification and Prioritization System.

The MVP supports anonymous civic complaints persisted through FastAPI in PostgreSQL. Issue #4 adds an accessible issue-location picker and requires a photo plus a confirmed issue location in the citizen frontend. The backend keeps both fields nullable so existing records and direct API clients remain compatible. Issues #9–#10 add protected municipal operations and responsive/accessibility hardening. Completed Issue #11 adds [departments, membership, accountable assignment and server-backed work queues](docs/ISSUE_011_DEPARTMENT_OWNERSHIP.md). Issue #12 adds a portable [production deployment](docs/DEPLOYMENT.md), protected evidence, private citizen tracking, readiness, backup/restore tooling and CI. Video, ML, classification, routing recommendations and priority logic remain deferred; see [MVP scope](docs/MVP_SCOPE.md).

Issue #5 establishes the research-data contract before model development. It versions the proposed `civicai-category-v1`, documents human annotation/adjudication, and validates provenance manifests for identity, annotation state, safe file references, SHA-256 hashes and split leakage. It does not claim an approved dataset or any model result. See [the research workspace](research/README.md) and [Issue #5 scope](docs/ISSUE_005_RESEARCH_DATA_FOUNDATION.md).

## Issue #4: accessible issue-location selection

Issue #6 is in progress: [India-only dataset audit and preparation](docs/ISSUE_006_DATA_PREPARATION.md) adds checksum-pinned OpenCity/IChangeMyCity acquisition, deterministic source auditing and leakage-aware split proposals. The local source has 16,071 Bengaluru text complaints but no images or approved CivicAI labels. A suitable paired Indian research dataset has not been acquired and ML training has not started. Commands are in [research/README.md](research/README.md).

Issue #7 Stage A is implemented: [offline human review](docs/ISSUE_007_HUMAN_REVIEW.md) generates ignored, checksum-bound CSV forms for taxonomy, mapping, privacy, record, duplicate, license and final approval decisions. No decision is prefilled, Stage B is waiting for real reviewers, and training remains prohibited.

Issue #8 adds the [municipal operations vertical slice](docs/ISSUE_008_MUNICIPAL_OPERATIONS.md): controlled lifecycle, immutable history, optimistic concurrency, a paginated/searchable/filterable operator queue, evidence/location detail and real operational counts. Issue #9 adds [real municipal authentication and RBAC](docs/ISSUE_009_AUTH_RBAC.md). Open `/admin`; unauthenticated users see `/admin/login`. Operators manage complaints and administrators additionally manage municipal accounts.

The citizen form and municipal workspace reflow from small phones through large desktops. Narrow municipal screens use complaint cards and a compact keyboard-operable menu; wider screens use the data table and full navigation. Every route has a meaningful title and unknown citizen/admin routes have contextual recovery pages. Accessibility work follows selected GIGW/WCAG patterns but is not a formal conformance claim.

## Municipal authentication

Apply migrations through `0007`, then create the first administrator interactively. The command uses `getpass`, validates a 12–128 character password, hashes it with Argon2id and refuses to run when an active administrator already exists. Do not put the password in a command argument or tracked file.

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m civicai.bootstrap_admin
```

Municipal sessions use a random opaque cookie and PostgreSQL session record. Only a SHA-256 digest of the authentication token is stored. The cookie is HttpOnly and SameSite=Strict; authenticated mutations also require a session-bound CSRF token and permitted browser Origin. Sessions expire absolutely after eight hours by default. Set `AUTH_COOKIE_SECURE=true` with `APP_ENV=production`; production startup refuses an insecure cookie. CivicAI intentionally enables no backend CORS middleware because the supported browser deployment is same-origin (Vite proxy locally, reverse proxy in production).

Citizens can explicitly search by locality, PIN code, street, address or landmark, use their current device position, and optionally refine the selected point on a map. Search results can be selected and confirmed without operating the map. The form identifies the selected location as exact, approximate or broad and requires confirmation after any map adjustment.

The frontend requires one valid JPEG/PNG photo and one confirmed location before submitting. This is a user-experience rule for the citizen form, not a breaking backend constraint: old location-free records and trusted direct API clients remain supported. A selected location describes the civic issue, not necessarily the reporter's current position. Nearby details should help municipal staff identify the site but must not contain private personal information.

With the default public-Nominatim fallback, search is sent only when the user presses Search or Enter. When `GEOCODING_PROVIDER=maptiler` and `MAPTILER_API_KEY` are configured, the frontend enables debounced search-as-you-type suggestions. If that same key is browser-origin restricted, `MAPTILER_REQUEST_ORIGIN` identifies the CivicAI origin on backend geocoding calls; production Compose derives it from `CIVICAI_SITE_ADDRESS`. The backend also supports reverse geocoding after the pin moves. Provider capabilities are discovered at runtime, so public Nominatim never receives autocomplete traffic. Both public geocoding modes are external dependencies without a CivicAI SLA.

The street map is lazy-loaded and uses Leaflet with MapTiler Streets v4 raster tiles. It supports desktop left-click, marker drag, touch pan/zoom and marker drag; the old directional controls are removed. Tiles use browser-public `VITE_MAPTILER_API_KEY`; there is no anonymous tile fallback. A one-key MapTiler account may use the same value for `MAPTILER_API_KEY` and `VITE_MAPTILER_API_KEY`; once compiled into JavaScript it is publicly observable and must be protected with MapTiler Allowed HTTP Origins/usage restrictions rather than secrecy. Separate values remain supported when the plan permits them. MapTiler and OpenStreetMap attribution remain visible. See `frontend/.env.example`, `.env.example` and `docs/ISSUE_004_LOCATION_SELECTION.md`.

## Issue #3: photos and location

After pulling, install updated backend dependencies with `python -m pip install -e ".[test]"` using the project virtual environment, run `python -m alembic upgrade head`, and run `npm install` in `frontend`. Restart both servers. Migrations 0002–0004 preserve existing complaints while adding nullable image, location-context, selection-source and device-accuracy fields.

POST now uses multipart/form-data, including for text-only submissions. JSON clients must migrate; see docs/API_CONTRACT.md. The frontend handles this automatically.

The citizen frontend requires one JPEG/PNG (5 MiB maximum); the backward-compatible API keeps it optional. Images must decode successfully and match their declared MIME, be at most 20 million pixels and have one frame. Re-encoding preserves orientation while removing EXIF/text metadata. Total multipart body is bounded to 5 MiB + 256 KiB, while Caddy rejects production requests above 6 MiB. Stored filenames are generated and original names ignored.

Files are stored under data/uploads/complaints locally and a private named evidence volume in production. `UPLOAD_DIR` can override the directory; the backend needs write permission. PostgreSQL stores only relative image references. Back up files and database together. Ordinary persistence failures clean up newly saved files; process crashes may leave orphan files. Issue #12 removes anonymous evidence access: the image route now requires a municipal session and complaint-level authorization. `python -m civicai.media_audit` reports missing/orphan evidence without deleting it.

Use “Use my current location” while near the issue. Permission is requested on demand. The browser may use a device fix from the last five minutes and waits up to 30 seconds for one. Browser location requires a secure context (HTTPS or trusted localhost), operating-system Location Services and an available location provider; on Windows, keep Location Services and Wi-Fi enabled. A failure preserves the draft and lets the citizen search for the issue instead. Location remains optional in the backward-compatible API but is required by the citizen form; it does not enter the current classification experiment.

Video and manual coordinate entry are not offered. Issue #4 provides a street map for refining a searched or device-derived location. Avoid real private evidence in the demonstration database.

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

Open http://127.0.0.1:8000/docs for the interactive API. Expand POST /api/v1/complaints, choose Try it out, enter a description and optional coordinates, and Execute. Save both the returned `complaint_id` and `tracking_token`; the status endpoint requires both. There is no anonymous global complaint list. `GET /health` reports process liveness and the safe release identifier; `GET /ready` checks PostgreSQL, migration head and evidence storage.

Schema creation uses Alembic, never automatic startup table creation. Complaint submission is anonymous; later status access requires the returned bearer capability. Every `/api/v1/admin/*` operation and evidence retrieval is authenticated server-side; account management additionally requires `municipal_admin`.

### Start the complete local MVP with one command

After completing the backend and frontend setup once, run this from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

The helper checks the backend and frontend first, starts only the service that is missing, waits for both ports, and verifies that the Vite API proxy returns JSON. Services are started as hidden local processes so closing this PowerShell window does not immediately stop the site. Runtime output is written to the ignored `logs` directory. Re-run the same command whenever http://127.0.0.1:5173 cannot be reached.

The backend defaults to port `8000`. If that port is already occupied by a stale or unrelated local process, set `BACKEND_PORT=8001` (or another free port) in the ignored root `.env` before starting. The startup helper and Vite proxy read the same setting, so browser API requests continue to reach the intended backend. Restart both affected development processes after changing the value. Do not add the MapTiler key or any other credential to a tracked file.

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

`VITE_MAPTILER_API_KEY` selects no provider: it supplies the browser-public credential for the fixed MapTiler Streets v4 raster endpoint. The map displays a configuration message rather than silently using an anonymous service when the key is absent; the production image build fails closed. In MapTiler, allow `localhost` for local verification (without scheme or port) and the actual CivicAI domain for deployment. The map code is loaded only after a location is selected. Do not add offline prefetching or bulk tile download. On this computer the global `npm` wrapper may fail because its roaming `npm-cli.js` is missing; the repository-local commands used for verification were `node .\node_modules\vitest\vitest.mjs run`, `node .\node_modules\typescript\bin\tsc -b`, and `node .\node_modules\vite\bin\vite.js build`.

### If the local frontend reports 404 or cannot reach the API

Run the repository startup helper first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

For a frontend that is already running but serving a stale proxy configuration, stop that frontend process and start it again from the `frontend` directory:

```powershell
npm run dev
```

The development proxy is loaded when Vite starts. Restarting is required after a stale development process or proxy-configuration change. A healthy proxy returns JSON from http://127.0.0.1:5173/health rather than the frontend HTML page. The anonymous complaint-list route is intentionally disabled.

## Production-like deployment

Production uses Docker Compose, Caddy HTTPS, the built React bundle, private FastAPI/PostgreSQL networking and persistent named volumes. It never runs Vite or exposes PostgreSQL/Uvicorn publicly. Start and stop with:

```powershell
Copy-Item .env.production.example .env.production
# Replace every placeholder, then:
.\scripts\start-production.ps1
.\scripts\stop-production.ps1
```

Do not use example values in production. Follow the full [deployment checklist](docs/DEPLOYMENT.md), [backup/restore procedure](docs/BACKUP_RESTORE.md) and [operations runbook](docs/OPERATIONS_RUNBOOK.md). `.env.production` and runtime backups are ignored by Git.

## Files

- backend/src/civicai: schemas, routes, service logic, persistence, configuration.
- backend/migrations: Alembic environment and migrations through 0007.
- backend/tests: API, migration consistency and database constraint tests.
- frontend/src: React complaint form, accessible location picker, lazy-loaded map, private tracking page, municipal workspace, API client, styles and interaction tests.
- scripts/start-dev.ps1: checks and starts both local development services, then verifies the API proxy.
- compose.production.yml, Dockerfile and deploy/: portable Caddy/FastAPI/PostgreSQL production topology.
- scripts/backup-production.ps1 and verify-backup-restore.ps1: coordinated runtime backup and disposable restore verification.
- docs: project context, [current state](docs/CURRENT_STATE.md), and [development log](docs/DEVELOPMENT_LOG.md).
- docs/reference/project-synopsis.docx: approved synopsis.
- research: proposed taxonomy, Indian-source acquisition/audit, annotation/data documentation and manifest/preparation validation; no approved training dataset or results yet.
- ml and data: reserved for later approved acquisition and experiment milestones.

[Public repository](https://github.com/Soumodeep-Das/civic-ai). Verified Issue #4 history is published on `main`; never rewrite shared history without explicit authorization.
