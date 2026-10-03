# Architecture

## Status and principles

This document defines a deliberately small architecture. The design favors clear component boundaries, replaceable future ML models, testability, and a vertical-slice delivery sequence.

Issue #1 implementation lives in backend/src/civicai: routes.py delegates to service.py; schemas.py handles HTTP validation/serialization; models.py and database.py handle SQLAlchemy persistence. domain.py defines complaint status and missing-record semantics. main.py owns application lifecycle and error handlers. Alembic migrations are separate from app startup. The backend, migration and persistence flow are locally verified; see CURRENT_STATE.md.

Issue #11 keeps ownership rules in `ownership.py`: routes authenticate/validate, ownership/service code enforces membership/concurrency/lifecycle rules, and SQLAlchemy/PostgreSQL atomically update current assignment plus immutable business history. Authentication role and organizational membership remain separate. Queues are parameterized database views over complaints, never copied records. Citizen schemas continue to exclude internal ownership.

## Intended system

```text
Citizen/Admin browser
        |
        v
    React web app
        |
        v
   FastAPI application
     |      |       |
     |      |       +--> ML inference adapter (later milestone)
     |      +----------> image/file storage adapter (later milestone)
     +-----------------> PostgreSQL
```

The browser will communicate with the backend through a versioned JSON API. The backend will own validation, application rules, authorization when introduced, persistence, and orchestration of ML inference. React must not connect directly to the database or model files.

## Planned components

### Frontend

Issue #2 implements a single-page React and TypeScript interface for anonymous complaint submission. Issue #12 removes the earlier anonymous recent-complaint feed and adds a private capability status page. `frontend/src/api/complaints.ts` owns HTTP access; React owns the small amount of form and request state. Vite proxies `/api`, `/health` and `/ready` to local FastAPI only during development, avoiding a backend CORS change.

Issue #4 adds a bounded location-selection component. Text search and current-device capture both produce one selected candidate; confirmation is separate from map adjustment. The lazy-loaded Leaflet renderer consumes normalized coordinates and never calls the geocoder directly. Desktop click, marker drag and touch interaction converge on the same location state, and every coordinate change invalidates prior confirmation. Raster rendering was selected after the WebGL vector canvas stayed blank in the actual in-app browser despite loading its style and attribution. Production tiles use MapTiler Streets v4 through browser-public, origin-restricted `VITE_MAPTILER_API_KEY`. A one-key plan may reuse `MAPTILER_API_KEY`; Compose supports that current deployment while retaining a distinct frontend override for future plans. No anonymous raster service is a production fallback.

Issue #8 keeps one React application with citizen (`/`) and municipal (`/admin`, `/admin/complaints`, `/admin/complaints/:id`) routes. The detail map reuses the lazy Leaflet component in read-only mode, preserving submitted location evidence. Components leave room for later AI sections but render no prediction placeholders or fake values.

### Backend

A FastAPI service will expose API endpoints, validate input, apply complaint workflow rules, and coordinate persistence and later inference. Domain logic should remain separate from HTTP handlers and database-specific code.

Issue #4 adds provider-neutral search, reverse-geocoding and capability endpoints. Provider response parsing, throttling and caching stay outside route handlers. A Nominatim-compatible adapter supplies policy-limited explicit search; a server-configured MapTiler adapter supplies autocomplete and reverse geocoding. The browser receives only CivicAI's normalized geocoding contracts, but its MapTiler tile key is intentionally compiled into the frontend. When one account key supplies both functions, that shared credential is public and must be origin/usage restricted. Because MapTiler rejects origin-restricted requests that omit origin identification, the backend sends the configured CivicAI `MAPTILER_REQUEST_ORIGIN`; production Compose derives it from the public site address. Neither provider is treated as a CivicAI-owned SLA.

Issue #8 adds a small domain state machine and municipal query/update services. Routes validate transport parameters; service code owns pagination, escaped search, real aggregates, transition rules and compare-and-set status updates. Repeating the current state is idempotent; stale `updated_at` fails with a sanitized conflict.

### Database

PostgreSQL will store complaint records and workflow state. Geospatial extensions are not required for the first vertical slice; PostGIS may be evaluated later if context-aware location queries justify it.

Migration 0005 expands the status constraint and creates append-only `complaint_status_events`. Existing rows receive creation events at their original timestamps. A database trigger rejects event update/delete; indexes support newest-first pagination, status filtering and per-complaint history. No municipal endpoint edits original citizen evidence/location.

### Media storage

Issue #3 uses uploads.py for bounded JPEG/PNG validation, re-encoding and local storage under data/uploads/complaints (UPLOAD_DIR override). PostgreSQL stores a nullable image_ref. Multipart creation coordinates validation, file storage and complaint persistence. Issue #12 places production evidence in a private persistent volume and requires municipal authentication plus complaint authorization on the API image route. A read-only audit reports reference/file inconsistency; legal retention and automatic deletion remain unresolved.

### ML pipeline

Training/evaluation code and online inference are separate concerns. Experiments will create versioned model artifacts and reports; the application will eventually call a narrow inference interface. Models must not be trained inside an API request.

Issue #5 adds the pre-training data boundary under `research/`. Restricted text and image files remain outside Git; a JSONL manifest references them with source/provenance metadata, taxonomy and annotation state, group identity, frozen split and SHA-256 hashes. The standalone validator rejects schema drift, unsafe paths and exact group/content leakage before later experiment code reads a dataset. A successful manifest check establishes internal consistency only—not license, consent, representativeness or label correctness.

Issue #6 adds an India-only source boundary. `opencity.py` performs bounded, checksum-pinned acquisition into an ignored immutable snapshot; `audit.py` emits aggregate diagnostics and privacy-conscious review references; `prepare.py` admits only explicitly reviewed Indian source identifiers and builds leakage-aware split proposals. Source labels remain separate from CivicAI annotations throughout. `COMPLETE`/`INCOMPLETE` markers prevent interrupted acquisition or preparation directories from being treated as releases. None of these gates authorizes training by itself.

Issue #7 Stage A adds an offline review boundary. `review.py` generates checksum-bound local CSV forms, validates partial independent submissions, merges matching decisions and quarantines conflicts for adjudication. `curate.py` contains deterministic derived-text redaction and a fail-closed readiness report; it does not yet publish a curated dataset. Review artifacts remain under ignored data directories. Only a later Stage B may convert validated human decisions into a new versioned derivative.

Issue #9 adds a security boundary around the Issue #8 municipal surface. `municipal_users`, `municipal_sessions` and `security_audit_events` remain separate from anonymous citizen complaints. The browser receives an opaque HttpOnly cookie; PostgreSQL stores only its SHA-256 digest plus expiry, revocation and a session-bound CSRF secret. Authentication dependencies load the current active user on every protected request, so disable and role changes take effect without trusting frontend state. Operator and administrator authorization is enforced in FastAPI; `/admin/users` is administrator-only. Complaint history retains a nullable municipal-user foreign key so pre-authentication history is not rewritten.

The frontend calls `/api/v1/auth/me` on every municipal startup or refresh. It keeps the returned CSRF token only in React memory, sends it on authenticated mutations, and shows login after 401 or expiry. It never stores bearer credentials in localStorage. Citizen and administrative response schemas remain distinct: citizen responses omit immutable history and internal operator notes.

Issue #10 keeps that boundary and adds a presentation architecture rather than a service layer. The root route eagerly loads only the citizen shell; `AdminApp` is a route-level lazy chunk, while `LocationMap` remains a separate lazy chunk. Shared `StatusBadge` and `ConfirmDialog` primitives plus CSS tokens standardize semantics and interactions without a component framework. Native routes remain intentionally small: exact citizen/admin matches render their views and unknown paths render contextual 404 recovery pages.

Responsive behavior is content-driven. Citizen work is single-column first and becomes a bounded split workspace on wide screens. Municipal results have two representations over the same API data: an accessible desktop table and task-focused mobile cards selected by CSS at the layout breakpoint. This avoids duplicating fetch/state logic while preventing page-level horizontal scrolling. Textual place evidence is authoritative when map tiles fail. Evidence images reserve dimensions and load lazily; original stored bytes are never transformed by the frontend.

## MVP vertical slice

Issue #6's offline `research.civicai_research.prepare` consumes a local manifest and immutable raw files. It emits a new proposal manifest/report under ignored processed data, with verified hashes, duplicate components and support counts. This tooling does not connect to the complaint database or grant training approval. Acquisition and source-specific import mappings remain outstanding.

Issue #1 established the tested backend persistence flow and Issue #2 completed the smallest browser-to-database product. Issues #3 and #4 add bounded image evidence and accurate issue-location capture without introducing accounts, prioritization, department routing or ML. The original MVP boundary and acceptance criteria remain documented in `MVP_SCOPE.md`.

## Cross-cutting requirements

- Validate all external input and handle errors consistently.
- Keep secrets in environment configuration and outside Git.
- Use migrations for database changes once persistence begins.
- Record timestamps in UTC and define display-time conversion separately.
- Use stable identifiers rather than user-visible sequence assumptions.
- Log operational events without recording sensitive complaint text or coordinates unnecessarily.
- Add authorization before exposing administrative or personally identifying data.

## Production deployment

Issue #12 selects a portable single-host Docker Compose topology: Caddy is the only public service and terminates HTTPS, serves the immutable Vite build and proxies API/health paths; private Uvicorn serves FastAPI; private PostgreSQL and separate evidence storage use named volumes. A one-shot Alembic service gates backend startup. Caddy state is persistent. Neither the source tree, Git metadata, secrets nor research data enters runtime images/volumes.

The private network pins Caddy at `172.28.0.10`; Uvicorn trusts forwarded headers only from that address. Changing the network requires changing this allowlist. Caddy handles backend paths before SPA fallback. It applies a 6 MiB outer body limit, compression, minimal CSP/security headers, no-store HTML and immutable fingerprinted-asset caching. Vite is never a production process.

`/health` is process liveness with a safe release identifier. `/ready` checks database connectivity, migration `0007` and writable evidence storage but not optional geocoding. Production configuration rejects insecure cookies, non-HTTPS allowed origins, weak/default tracking secrets and unsafe evidence paths. Compose rotates JSON logs and exposes neither PostgreSQL nor Uvicorn host ports.

The topology intentionally remains platform-neutral and single-host. It does not provide high availability, a distributed rate limiter, legal retention automation, cloud object storage, external metrics/log aggregation or automated deployment. See `DEPLOYMENT.md`, `BACKUP_RESTORE.md` and `OPERATIONS_RUNBOOK.md`.
