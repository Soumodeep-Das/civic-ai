# Development Log

## 2026-09-21 — Issue #4 interaction refinement completed

Implemented the accepted autocomplete and pin-refinement design without breaking the existing complaint endpoints. Added the MapTiler search/reverse adapter, provider capability discovery, 350 ms debounced typeahead for capable providers, explicit-search fallback for public Nominatim, keyboard-accessible suggestions, reverse geocoding after pin movement, and persisted `search`/`device`/`map` source plus optional device accuracy through additive migration 0004. Development PostgreSQL reports `0004 (head)` and the eight existing complaints remain intact.

The first live map refinement used MapLibre with OpenFreeMap. Its style, marker and attribution loaded, but the WebGL canvas remained blank in the actual in-app browser. Replaced only the renderer with lazy-loaded Leaflet and configurable raster tiles; standard OpenStreetMap tiles are the local-demo default under its interactive-use policy. Live verification now visibly shows Belghoria Expressway, nearby roads/buildings, zoom controls, attribution and the draggable marker after selecting a Baranagar suggestion. No complaint was submitted during this verification.

Final regression: 79 backend tests passed with the same three dependency deprecations and known pytest cache-permission warning; migration 0004 is at head; 24 frontend tests passed; TypeScript compilation and the production build passed. The production build contains an approximately 238 kB initial JavaScript bundle and a 151 kB lazy map chunk. npm's audit reported zero known vulnerabilities when the new renderer dependency was resolved. Full autocomplete remains deliberately inactive until the user configures a MapTiler key in the ignored `.env`; explicit search, selection and the working street map are available now. The interaction suite also verifies that an in-flight response cannot repopulate stale suggestions after the user edits the query.

## 2026-09-20 — Issue #4 scope and architecture checkpoint

Accepted an accessible issue-location flow: explicit search by locality/PIN/street/address/landmark, current device location, optional map refinement and plain-language nearby details. Photo plus confirmed location become required in the citizen frontend, while the proven backend remains compatible with old rows and direct clients. Additive migration 0003 will preserve all prior data.

Reviewed FixMyStreet, W3C Geolocation, MapLibre, OSMF Nominatim policy and Google Places documentation. Selected a provider-neutral backend boundary with a policy-limited Nominatim-compatible local-demo adapter and an independently replaceable map renderer. Full criteria, edge cases, sources and exclusions are recorded in `ISSUE_004_LOCATION_SELECTION.md`. No production geocoding SLA, routing or Google billing dependency is claimed.

### Backend checkpoint

Added migration 0003, nullable human-readable location context, controlled precision and an explicit location-search endpoint. Search provider parsing, one-request-per-second pacing and a 15-minute bounded cache are isolated in `geocoding.py`; tests inject a fake or mock transport and make no external calls. Development migration reached 0003 head. Full backend suite passed 62 tests. A first run failed only because the ignored `tmp` parent directory did not exist; after creating that local directory the conclusive suite passed. Dependency refresh initially hit the network sandbox, then network access was granted for package retrieval; installed runtime packages already supported the test run.

### Frontend checkpoint

Added explicit place/PIN/street/landmark search, current-device capture, nearby details, explicit confirmation and an optional MapLibre map with pointer, drag and keyboard adjustment. The citizen form now requires a valid photo and confirmed issue location while the backend remains backward compatible. Search is explicit rather than autocomplete, map loading is optional, and stale browser-location callbacks cannot replace a newer user selection.

MapLibre 6.10 is locked in the frontend package lock; npm reported zero known vulnerabilities at installation. The host's global npm wrapper still points to a missing roaming `npm-cli.js`, so repository-local Node entry points were used. All 20 frontend interaction tests passed, TypeScript compilation passed and the production build succeeded. Lazy loading reduced initial JavaScript from about 1.27 MB to 236 kB. The optional map chunk remains about 1.03 MB and triggers Vite's non-blocking size advisory.

Live verification searched for Baranagar Municipality through the real backend adapter and returned a relevant result. Search-only selection, on-demand map loading, keyboard adjustment, confirmation invalidation/reconfirmation and missing-description/photo feedback were exercised in the browser. No complaint was submitted during this checkpoint.

### Final regression

Development PostgreSQL reports migration 0003 at head. The complete backend suite passed 62 tests and the complete frontend suite passed 20 tests; TypeScript compilation and the production build passed. Backend output contains the same three dependency deprecations plus the known local pytest cache-permission warning. The build contains a 236 kB initial JavaScript bundle and a lazy 1.03 MB map chunk; Vite's warning applies only to that optional chunk. No Issue #1 complaint behavior was changed and no Issue #5 work was started.

## 2026-09-20 — Location timeout correction

Reproduced the user-visible condition where browser location permission was granted but the application reported a timeout. The frontend imposed a fresh-only ten-second acquisition deadline; permission grants access but do not guarantee that Windows can supply a position within that deadline. W3C, MDN and Microsoft guidance was reviewed and recorded in `ISSUE_003_EDGE_CASES.md`.

Location capture now accepts a device fix no older than five minutes and waits up to 30 seconds. The timeout message explains that device Location Services and Wi-Fi may still be needed. Location remains explicit, optional and omitted after any failure. Frontend tests assert the acquisition policy and preserve denial, unavailable-provider, timeout and late-callback behavior. Live verification results follow after the automated checks.

Verification: all 15 frontend tests passed and the production build succeeded using the repository-local Node binaries; the host's global npm launcher remains broken because its roaming `npm-cli.js` target is missing. The first live request still returned `TIMEOUT`. Read-only observations showed the Windows Location Service running, machine consent allowed and desktop-app consent allowed, while one current-user registry value reported `Deny`; this was initially treated as a likely block and the Windows Location settings page was opened. No system privacy setting was changed automatically.

Final live verification succeeded after the user reviewed Windows settings. The browser displayed “Location captured successfully,” a photo complaint was submitted, the UI marked it “Location provided,” and the complaint API returned both coordinates for record `b7853642`. The user independently confirmed latitude and longitude persistence in pgAdmin. The same registry value still reported `Deny` after success, proving it is not authoritative for this desktop-browser path; future diagnosis must rely on the live browser API rather than inferring access from that value. Issue #3's location path is now locally verified.

## 2026-09-20 — Local MVP availability fix

The reported browser “site can't be reached” failure was reproduced. FastAPI remained healthy on port 8000, but no process was listening on the Vite port 5173; the earlier frontend development process had ended. This was a local process-lifecycle failure rather than an Issue #3 complaint-flow defect.

Added `scripts/start-dev.ps1` as a repeatable repository-root command. It checks both services, starts only missing services as hidden local processes, waits for readiness and rejects a broken Vite proxy unless the complaint-list endpoint returns JSON. README setup and troubleshooting now point to this command. After the fix, the frontend root, backend health endpoint and proxied complaint-list endpoint were all rechecked successfully.

## 2026-09-20 — Issue #3 frontend and edge-case verification

Final checks: 42 backend tests passed with the same three non-blocking dependency deprecations; 15 frontend tests passed; production build succeeded. The managed Windows default pytest temp folder became inaccessible, so the conclusive backend run used a fresh `--basetemp` under the workspace. Diff whitespace checks passed and no runtime upload was staged. Branch publication is left to the user per their prior instruction.

Backend checkpoint 916cb3e added multipart and image persistence. React now supports photo selection/removal, image display and permission-based location capture. The form can submit after capture failure and invalidates late callbacks after omission/submission. Automatic POST retries are not used.

Migration 0002 applied to development PostgreSQL; four existing records remained. Browser-created photo record 523a4bf2 and text-only record 3127b31a survived reload. The image loaded successfully and PostgreSQL confirmed the stored reference. An actual browser location request timed out; text submission after timeout succeeded. Successful device capture and the native denial prompt remain manually unverified; automated tests cover those outcomes. Browser console was clear.

Research from FixMyStreet, MDN and OWASP is recorded in ISSUE_003_EDGE_CASES.md. Permanent project instructions now require online edge-case and comparable-product research for every feature. Added storage-failure, database-cleanup, metadata-removal and total-body-limit tests. Corrected the HTML ignore rule so the frontend entry file is included in fresh clones.


## 2026-09-20 — Issue #3 backend checkpoint

Implemented multipart submission, optional image_ref migration 0002, bounded JPEG/PNG decoding and storage, safe image retrieval and isolated temporary upload storage in tests. 38 backend tests passed; final size-guard rerun and development migration remain pending. Frontend integration is next. Existing Issue #1 warnings remain non-blocking.


This log records engineering checkpoints and reproducible evidence. It is not a research-results log.

## 2026-09-20 — Issue #1 verified locally

- PostgreSQL development and dedicated test databases configured.
- Alembic migration `0001` applied successfully.
- Full suite passed: 27/27 tests.
- FastAPI application started successfully.
- `GET /health` returned `200 {"status":"ok"}`.
- Complaint create, retrieve and list endpoints returned their expected success responses.
- Created complaint persistence was confirmed in PostgreSQL.

No Issue #1 behavior was changed during this documentation checkpoint.

### Non-blocking dependency deprecation warnings

1. FastAPI's test client reported that using `httpx` with `starlette.testclient` is deprecated and recommends `httpx2`.
2. Starlette's test client uses the deprecated `anyio.abc.BlockingPortal` alias instead of `anyio.from_thread.BlockingPortal`.
3. Alembic reported legacy `prepend_sys_path` splitting because `path_separator` is not set in `alembic.ini`.

The warnings did not fail tests or affect the verified complaint flow. They are recorded for deliberate dependency/configuration maintenance rather than being suppressed or addressed by changing Issue #1 behavior.

## 2026-09-20 — Issue #2 started

User direction narrowed all implementation to the MVP in `MVP_SCOPE.md`. Issue #2 supplies its visible frontend half.

- Added a React 19 and TypeScript interface using Vite.
- Added anonymous complaint submission with optional coordinate validation.
- Added stored-complaint loading, empty, retry, success and failure states.
- Added six frontend interaction tests; all pass.
- Created a successful production build.
- Inspected the live browser against the local backend; an existing PostgreSQL complaint rendered and the browser reported no console errors.
- Submitted the demonstration complaint `MVP verification: damaged streetlight near the community park` through the browser. The API returned reference prefix `f5c85b80`, and the persisted complaint appeared immediately in the live queue.
- No Issue #1 API or database behavior was changed.

The initial Vitest run could not start its default fork worker in the managed workspace. Configuring a single worker-thread pool made the test process compatible with the environment; this changes test execution only, not product behavior.

The MVP checkpoint was committed locally as `f4ad009` on `feat/frontend-complaint-flow`. Remote fetch succeeds, but push exits with code 128 because this terminal has no usable GitHub authentication. No force push or history rewrite was attempted; the browser-visible public repository is unchanged.

## 2026-09-20 — MVP workflow 404 recheck

The user reported a 404 while submitting a complaint. Direct checks showed the FastAPI health and complaint-list endpoints returning 200 with PostgreSQL data, while the existing Vite process returned the frontend HTML page for `/api/v1/complaints` instead of proxying it. This affected both list and submit requests.

A clean restart of the Vite development server restored the configured proxy. Verification after restart:

- `GET http://127.0.0.1:5173/api/v1/complaints` returned 200 JSON.
- `GET http://127.0.0.1:5173/health` returned `200 {"status":"ok"}`.
- Browser submission created complaint reference prefix `0fb72197`.
- The submitted text `Workflow recheck: blocked storm drain near the market` appeared immediately in the queue, which increased from two to three stored complaints.

No backend, database or product-code defect was found, so Issue #1 behavior was not altered. README troubleshooting now records the frontend restart procedure.
