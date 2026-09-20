# Architecture

## Status and principles

This document defines a deliberately small architecture. The design favors clear component boundaries, replaceable future ML models, testability, and a vertical-slice delivery sequence.

Issue #1 implementation lives in backend/src/civicai: routes.py delegates to service.py; schemas.py handles HTTP validation/serialization; models.py and database.py handle SQLAlchemy persistence. domain.py defines complaint status and missing-record semantics. main.py owns application lifecycle and error handlers. Alembic migrations are separate from app startup. The backend, migration and persistence flow are locally verified; see CURRENT_STATE.md.

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

Issue #2 implements a single-page React and TypeScript interface for anonymous complaint submission and the recent complaint list. `frontend/src/api/complaints.ts` owns HTTP access; the React component owns the small amount of form and request state. Vite proxies `/api` and `/health` to the local FastAPI server during development, avoiding a backend CORS change. No router, component library, global state library or map provider is needed for the MVP.

Issue #4 adds a bounded location-selection component. Text search and current-device capture both produce one selected candidate; confirmation is separate from optional map adjustment. The lazy-loaded map renderer consumes normalized coordinates and never calls the geocoder directly. Pointer, marker-drag and keyboard controls converge on the same location state, and every coordinate change invalidates prior confirmation.

### Backend

A FastAPI service will expose API endpoints, validate input, apply complaint workflow rules, and coordinate persistence and later inference. Domain logic should remain separate from HTTP handlers and database-specific code.

Issue #4 adds a provider-neutral geocoding service and a small API endpoint. Provider response parsing, throttling and caching stay outside route handlers. The first adapter is Nominatim-compatible and configured through environment variables; the browser receives only CivicAI's normalized result contract. The adapter is a local-demo dependency, not a promised production SLA.

### Database

PostgreSQL will store complaint records and workflow state. Geospatial extensions are not required for the first vertical slice; PostGIS may be evaluated later if context-aware location queries justify it.

### Media storage

Issue #3 uses uploads.py for bounded JPEG/PNG validation, re-encoding and local storage under data/uploads/complaints (UPLOAD_DIR override). PostgreSQL stores a nullable image_ref. A restricted API image route serves raster content. Multipart creation coordinates validation, file storage and complaint persistence. This remains a local anonymous demonstration; production retention, quotas, authorization and orphan recovery are unresolved.

### ML pipeline

Training/evaluation code and online inference are separate concerns. Experiments will create versioned model artifacts and reports; the application will eventually call a narrow inference interface. Models must not be trained inside an API request.

## MVP vertical slice

Issue #1 established the tested backend persistence flow. Issue #2 adds the browser form and stored-complaint list to complete the smallest end-to-end product. The binding boundary and acceptance criteria are in `MVP_SCOPE.md`. Authentication, uploads, mapping, prioritization, department routing and ML remain deferred.

## Cross-cutting requirements

- Validate all external input and handle errors consistently.
- Keep secrets in environment configuration and outside Git.
- Use migrations for database changes once persistence begins.
- Record timestamps in UTC and define display-time conversion separately.
- Use stable identifiers rather than user-visible sequence assumptions.
- Log operational events without recording sensitive complaint text or coordinates unnecessarily.
- Add authorization before exposing administrative or personally identifying data.

## Deployment

No cloud platform, container strategy, CI provider, domain, or production topology has been selected. Deployment decisions should follow a working local vertical slice and be logged in `DECISIONS.md`.
