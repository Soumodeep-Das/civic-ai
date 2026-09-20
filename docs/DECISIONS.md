# Decision Log

Only decisions actually made are recorded here. Proposed choices remain in the relevant design document until accepted. Each future entry should include context, decision, consequences, status, and date.

## D001 Separate classification from prioritization

- Date: 2026-09-19
- Status: accepted
- Decision: Complaint category classification and complaint prioritization are separate tasks. Category alone will not determine priority.
- Consequence: Data labels, model outputs, API fields, evaluation, and user explanations must preserve this distinction.

## D002 Minor research uses modality comparison

- Date: 2026-09-19
- Status: accepted
- Decision: The minor-project research will compare text-only, image-only, and text-image multimodal classification under controlled evaluation.
- Consequence: The dataset and split design must support fair aligned comparisons. No modality is presumed superior.

## D003 Transparent priority now and learned context later

- Date: 2026-09-19
- Status: accepted
- Decision: The approved prototype includes a separate, transparent contextual priority mechanism with human verification. Learned ranking and richer spatial-temporal prioritization are future major-project research.
- Consequence: The minor implementation may add documented scoring only after category and priority labels are defined; it must not be presented as validated ML without evidence.

## D004 Technology direction

- Date: 2026-09-19
- Status: accepted as direction
- Decision: Use React for the frontend, Python with FastAPI for the backend, PostgreSQL for persistence, and Python ML libraries selected according to experimental need.
- Consequence: A material change requires a new decision entry that explains benefits, drawbacks, and migration impact.

## D005 Milestone-driven delivery

- Date: 2026-09-19
- Status: accepted
- Decision: Build through small, reviewed vertical slices. The first planned slice is complaint submission through API and database persistence to an administrative list.
- Consequence: No full-stack or ML scaffolding is created during the foundation task.

## D006 Evidence and research integrity

- Date: 2026-09-19
- Status: accepted
- Decision: Citations, dataset rights, labels, metrics, findings, statistical claims, and novelty statements must be traceable to verified sources or reproducible project outputs.
- Consequence: Placeholder or invented results are prohibited, and limitations must be reported.

## D007 Issue 1 runtime and dependency management

- Date: 2026-09-19
- Status: accepted; runtime verified 2026-09-20
- Decision: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Psycopg 3, Alembic and pytest. Use setuptools/pyproject.toml and pip editable installation with a test extra.
- Consequence: No uv requirement. Supported dependency ranges are declared and locally installed; a resolved lock file remains pending. Current non-blocking dependency deprecations are tracked in `DEVELOPMENT_LOG.md`.

## D008 Anonymous first complaint API

- Date: 2026-09-19
- Status: accepted by Issue 1
- Decision: Create, retrieve and list complaints anonymously, with exactly the seven fields authorized in the issue. Only submitted status is allowed; status transitions are deferred.
- Consequence: Use demonstration data locally. Trim descriptions; reject extra fields; coordinates are independently optional. Lists are ordered and unpaginated. UUIDs are application-generated; PostgreSQL initializes timezone-aware timestamps. SQLAlchemy updates updated_at on future ORM updates; direct SQL update tracking is not implemented.

## D009 PostgreSQL migrations and test isolation

- Date: 2026-09-19
- Status: accepted; execution verified 2026-09-20
- Decision: Alembic owns schema changes. Tests use real PostgreSQL, not SQLite. Require a separate database ending in _test, create a uniquely named schema, apply migrations, roll back each API test, and drop only that schema after the suite.
- Consequence: Test role needs CREATE SCHEMA permission; missing configuration fails instead of skipping. No normal developer database is modified by tests. Database constraints defend text, coordinates and status in addition to HTTP validation.

## D010 Health and error contract

- Date: 2026-09-19
- Status: accepted
- Decision: GET /health reports liveness only; operational database failures return a sanitized 503 on complaint routes. Use code/message error objects, adding field details for validation failures.
- Consequence: Health does not certify database readiness. No credentials or raw request values are included in error responses.

## D011 MVP before feature expansion

- Date: 2026-09-20
- Status: accepted by user direction
- Decision: Complete and accept the anonymous complaint submission-to-persisted-list workflow as the sole MVP before implementing any broader synopsis capability.
- Consequence: Authentication, images, maps, ML, classification, prioritization, routing, analytics and deployment work are deferred. `MVP_SCOPE.md` is the binding scope for the active work.

## D012 Minimal frontend stack and local API proxy

- Date: 2026-09-20
- Status: accepted for Issue #2
- Decision: Use React 19, TypeScript, Vite and Vitest with Testing Library. Keep request code in a small API client and use Vite's local proxy for the existing `/api` and `/health` paths.
- Consequence: The MVP needs no router, component library, global state library or backend CORS change. Node.js 22.12 or newer is required. npm manages and locks frontend dependencies.
