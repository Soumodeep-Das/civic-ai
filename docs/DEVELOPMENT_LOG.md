# Development Log

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
