# Architecture

## Status and principles

This document defines an intended, deliberately small architecture. It is not an implementation report. The design favors clear component boundaries, replaceable ML models, testability, and a vertical-slice delivery sequence.

Issue #1 implementation lives in backend/src/civicai: routes.py delegates to service.py; schemas.py handles HTTP validation/serialization; models.py and database.py handle SQLAlchemy persistence. domain.py defines complaint status and missing-record semantics. main.py owns application lifecycle and error handlers. Alembic migrations are separate from app startup. Runtime verification is pending; see CURRENT_STATE.md.

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

A React application will eventually provide citizen complaint submission and tracking plus an administrative complaint list. Route structure, component library, state-management approach, mapping provider, and accessibility baseline are unresolved.

### Backend

A FastAPI service will expose API endpoints, validate input, apply complaint workflow rules, and coordinate persistence and later inference. Domain logic should remain separate from HTTP handlers and database-specific code.

### Database

PostgreSQL will store complaint records and workflow state. Geospatial extensions are not required for the first vertical slice; PostGIS may be evaluated later if context-aware location queries justify it.

### Media storage

Images should be represented by metadata and a storage reference rather than database blobs unless later evidence supports another choice. Local development storage and any production object store remain undecided. Upload validation, privacy, retention, and access control must be designed before accepting images.

### ML pipeline

Training/evaluation code and online inference are separate concerns. Experiments will create versioned model artifacts and reports; the application will eventually call a narrow inference interface. Models must not be trained inside an API request.

## First vertical slice

The first implementation issue should establish one complaint domain model and the smallest tested backend persistence flow. It should exclude frontend scaffolding, authentication, uploads, mapping, prioritization, department routing, and ML; those approved synopsis capabilities follow in later milestones.

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
