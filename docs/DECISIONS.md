# Decision Log

## D029 Separate citizen identity and explicit municipal authority (2026-10-03, accepted)

- Citizens self-register; staff remain bootstrap/invitation-only.
- Preserve `municipal_users` and evolve the session table instead of rewriting proven RBAC/history.
- Use 15–128 character citizen passwords, Argon2id, bounded common-password blocking and no composition/rotation rule.
- Normalize email by trim plus lowercase comparison; never apply provider-specific transformations.
- Store action tokens hashed, single-use and time-limited; reset revokes citizen sessions.
- Use Google authorization-code OIDC, JWKS signature validation, state/nonce and issuer+subject; refuse email-only linking.
- Use captured development mail and configurable production SMTP through `EmailService`.
- Use `/municipal` and `/staff/sign-in` visibly while preserving `/admin` compatibility.
- Defer explicit federation linking, staff Google login, MFA, account deletion and notifications.

## D028 Separate public MapTiler tile credential (2026-10-02, accepted)

- Context: Production-like browser verification showed OpenStreetMap `Access blocked / 403` tiles when `tile.openstreetmap.org` was compiled as the production default. OSM policy must not be bypassed or spoofed.
- Decision: Use `MAPTILER_API_KEY` for FastAPI geocoding and `VITE_MAPTILER_API_KEY` for Leaflet MapTiler Streets v4 tiles. Because the current plan allows one active key, Compose defaults the Vite value to `MAPTILER_API_KEY`; a distinct override remains supported later. Any reused/browser value is public, requires MapTiler Allowed HTTP Origin/usage restrictions, preserves MapTiler/OpenStreetMap attribution, and is the only external image origin allowed by CSP. Set `MAPTILER_REQUEST_ORIGIN` on backend geocoding requests so the provider accepts the origin-restricted shared key. Fail the production frontend build when neither value exists and provide no anonymous tile fallback.
- Consequence: Local production-like use requires `localhost` in the browser-used key's allowed origins; real deployment requires the actual CivicAI domain. The current shared credential cannot be considered server-secret. A provider account/quota remains an operational dependency; plans with multiple keys can restore credential separation without code changes.

## D027 Portable production and private evidence boundary (2026-10-02, accepted)

- Deploy one Caddy → private FastAPI/Uvicorn → private PostgreSQL Compose topology on a normal single host. Serve the multi-stage Vite build from Caddy; never run Vite or publish Uvicorn/PostgreSQL in production. Use deliberate one-shot Alembic migration and persistent database/evidence/Caddy volumes.
- Trust forwarded headers only from Caddy's fixed private address. Require genuine HTTPS, Secure/HttpOnly/SameSite=Strict host-only cookies, existing CSRF/origin enforcement, a 6 MiB proxy limit, derived CSP/security headers and bounded container logs.
- Fail closed in production for weak/default capability secret, insecure cookie, non-HTTPS origin, invalid environment/release/log settings or non-absolute evidence storage. Keep provider/database secrets out of images, Git and logs.
- Remove the anonymous global complaint feed. Give the submitter an HMAC-SHA-256 bearer capability and expose only UUID, description, status and timestamps through that private link. Never expose coordinates, location labels, evidence, ownership or internal history there. Require municipal complaint authorization for every evidence response.
- Use coordinated `pg_dump` plus evidence archive backups and require disposable restore testing. Report media inconsistencies with a read-only tool; never delete solely from one audit. Treat sample backup rotation as an operational default, not legal retention law.
- Add a small GitHub Actions quality gate but no automatic deployment. Keep the deployment platform-neutral and research-isolated. Retain process-local login throttling as a documented single-instance limitation rather than adding Redis/custom Caddy plugins without measured need.

Consequences: the anonymous read API is intentionally breaking, existing tracking links did not exist and newly created links depend on preserving `PUBLIC_TRACKING_SECRET`. The topology is reproducible and recoverable but does not claim HA, zero downtime, legal compliance, provider SLA, centralized monitoring or distributed abuse protection.

## D026 Department ownership and accountable work queues (2026-10-02, accepted)

- Separate a complaint's nullable owning department from its nullable individual assignee. Use explicit many-to-many memberships independently from authentication roles; require an active assignee to be a current member of the active owning department.
- Preserve current state on complaints and append immutable assignment history in the same database transaction. Exact desired-state retries are idempotent; different stale writes fail through `expected_updated_at`.
- Let administrators manage/reassign all ownership and let operators view member-department/individual work and self-claim eligible unassigned department work. Keep citizen schemas free of ownership data.
- Block department deactivation and membership removal while they would strand unresolved work. Preserve disabled-user assignments and mark them inactive until an administrator explicitly reassigns.
- Add lightweight validated/generated request IDs and privacy-minimized local JSON request logs. Defer generic idempotency storage, external observability, boards, SLAs and automatic/ML routing.

## D025 Issue #10 public-service UX boundary (2026-10-02, accepted)

- Retain one-page citizen reporting and existing application contracts. Improve hierarchy, feedback, error recovery and responsiveness without adding a wizard, UI framework, backend migration or security relaxation.
- Use a compact CSS token/component vocabulary and mobile-first content breakpoints. Present municipal results as cards on narrow screens and the existing data table at wider widths; never make whole-page horizontal scrolling the normal phone interaction.
- Follow selected GIGW 3.0, WCAG 2.2, GOV.UK and USWDS patterns without claiming certification: semantic landmarks, skip links, route titles, visible focus, linked error summary plus inline errors, accessible dynamic status and text-plus-colour state labels.
- Warn before abandoning a meaningful unsent citizen draft, but never persist photo bytes or precise location in browser storage. Keep successful submission acknowledgement authoritative and avoid unearned service-time promises.
- Confirm only consequential operations: complaint rejection, municipal role changes and account disable. Dialogs must manage/trap/restore focus and support safe Escape cancellation.
- Lazy-load the municipal route and maps, lazy-load/reserve evidence media and use system fonts. Record local bundle evidence honestly; do not infer field Core Web Vitals.

Consequences: citizen visitors no longer download municipal code in the initial route, phone operators use a compact queue/navigation, and unknown routes recover clearly. Original evidence and all Issue #1–#9 backend/auth/research boundaries remain intact. PWA/offline, multilingual content, field performance monitoring and formal accessibility certification remain outside this issue.

## D024 Issue #9 municipal authentication boundary (2026-10-01, accepted)

- Use one first-party authentication model: opaque PostgreSQL-backed sessions in an HttpOnly, SameSite=Strict cookie. Store only the session-token SHA-256 digest; use eight-hour absolute expiry and database revocation. Avoid browser localStorage bearer tokens.
- Hash municipal passwords with Argon2id through `argon2-cffi` using OWASP's minimum profile (`m=19456 KiB`, `t=2`, `p=1`). Require 12–128 characters for this academic prototype; do not implement custom hashing or public registration.
- Keep exactly two municipal roles: `municipal_operator` for complaint operations and `municipal_admin` for those operations plus minimal account administration. Backend dependencies are authoritative; frontend visibility is only a usability reflection.
- Mitigate cookie-authenticated mutations with a random session-bound CSRF token in an `X-CSRF-Token` header, SameSite=Strict and exact Origin validation when supplied. Keep CORS disabled for the supported same-origin topology; any future separate origin requires an explicit reviewed allowlist.
- Use an in-process bounded per-IP and per-normalized-username login throttle for the single-instance prototype. A multi-instance production deployment must move throttling to shared infrastructure or a reverse proxy.
- Link new complaint status events to authenticated municipal users through a nullable foreign key. Preserve every historical null; do not fabricate actors.

Consequences: D023's unauthenticated municipal-route limitation is superseded. The citizen portal remains anonymous. Bootstrap is interactive with no shipped credentials, disabled users lose active sessions, final-admin/self-protection rules apply, and password reset/MFA/SSO remain outside this issue.

## D023 Issue #8 municipal lifecycle and audit boundary (2026-09-29, accepted)

- Use controlled states `submitted`, `under_review`, `in_progress`, `resolved` and `rejected`; allow resolved/rejected complaints to return to review. Same-state updates are idempotent. Do not model duplicate as a status; defer a separate relation/group compatible with future human/ML duplicate evidence.
- Append immutable creation/status-change events. Keep notes internal and actor nullable until real authentication exists. Never overwrite original citizen evidence/location.
- Require `expected_updated_at` for status mutation and use atomic compare-and-set to reject stale screens. This is bounded optimistic concurrency, not event sourcing.
- Keep one-based server pagination with 20 default/100 maximum and deterministic newest-first ordering. Use PostgreSQL with escaped substring search at current scale; no Elasticsearch/PostGIS/search extension yet.
- Calculate only real lifecycle/evidence/location totals. Add no ML category, priority, routing or confidence values until those contracts exist.
- Keep municipal endpoints visibly unauthenticated for the local prototype. Public exposure is prohibited until real identity/roles exist; a cosmetic login is not security.
- Keep Issue #7 Stage B paused and the verified research snapshot untouched.

Consequences: migration 0005 backfills history for existing complaints; citizen status remains truthful; authentication, assignment, public updates, appeals, duplicate relations and overview clustering remain deferred.

## D022 Issue #7 offline human-review gate (2026-09-27, accepted for Stage A)

- Use versioned local CSV forms plus machine validation instead of a new annotation web application. Raw complaint text, previews, submissions and merged decisions remain ignored; Git stores only schemas, code, hashes and aggregate documentation.
- Keep automated mapping proposals and previews separate from human decisions. Require pseudonymous reviewer ID, timezone timestamp, allowed state and decision-specific evidence. Support partial independent work and preserve disagreements for explicit adjudication.
- Treat taxonomy, mapping, privacy, record quality/language, duplicate grouping, license review and final dataset approval as separate gates. No single automated result or mapping proposal can set `training_approved` true.
- Escape formula-leading spreadsheet fields and instruct reviewers to use Protected View. This reduces but does not eliminate CSV/spreadsheet interpretation risk.
- Stage A stops after producing and validating review infrastructure. Stage B begins only with real reviewer submissions and may pause again if mapping review requires an expanded record-level queue.

## D021 Audited OpenCity snapshot remains a curation source (2026-09-27, accepted)

- Freeze the completed local IChangeMyCity snapshot by raw and metadata SHA-256; keep its source labels separate, CivicAI labels null and splits unassigned.
- Treat exact subcategory rules as versioned proposals with explicit `accepted`, `ambiguous`, `needs_review` and `rejected` states. Automated mapping never substitutes for record-level human review or approval.
- Keep raw text, coordinates, addresses and review queues outside Git. Store only aggregate audit evidence, hashes, code and documentation. Possible phone/email patterns require human privacy decisions before a derived release.
- Do not start training: severe proposed-class imbalance, Bengaluru-only scope, duplicate/template groups, ambiguous labels, no reliable `other` mapping and no Indian paired image source remain blocking research-design risks.

## D020 Indian civic data requirement (2026-09-27, user-directed)

- Train and evaluate CivicAI using civic incidents from India, with source/subset provenance verified. Foreign civic samples and translations of foreign incidents are excluded.
- The earlier 100-record Zurich discovery sample is retained only as ignored local exploration history; no model consumed it. Its acquisition code was discarded before commit.
- `prepare` rejects any source absent from the reviewed Indian source registry. Country acceptance does not grant label, privacy or training approval.
- OpenCity's Janaagraha/IChangeMyCity 2019–2022 log is accepted for local Indian text curation based on publisher provenance and stated CC BY-SA terms. It is not accepted as all-India representative, paired multimodal data, or independently verified labels.

## D019 Dataset preparation proposals and acquisition gate (2026-09-27)

- Preserve genuine text/image incident alignment; no generated descriptions or arbitrary same-class pairing in the primary modality comparison.
- Keep source categories, routing and resolution fields out of description inputs where they leak the target or future outcome.
- Connect related events and duplicate content before deterministic component assignment. Quarantine conflicting labels, report class/source/component support, and use paired eligibility by default.
- Treat hash-based 70/15/15 assignments as proposals with potentially uneven support. Final sample size, near-duplicate review and split suitability remain acceptance gates; do not tune seed using test performance.
- Acquire no unsuitable dataset merely to unblock training. OpenCity now supplies a possessed Indian text curation source, but no suitable eight-category paired collection or approved model-ready release exists. Issue #6 remains in progress.

## D018 Versioned research taxonomy and manifest gate (2026-09-27, accepted)

- Decision: freeze the eight working category identifiers as `civicai-category-v1`; require versioned annotation guidance and a strict provenance manifest before any training code consumes research data.
- Decision: keep restricted text/images outside Git and reference them with safe relative paths and SHA-256 hashes. Preserve `group_id` across related records and reject groups or exact modality hashes that cross assigned splits.
- Decision: allow curation states `pending`, `annotated`, `needs_adjudication` and `excluded`; only annotated records may enter train/validation/test. Category remains separate from severity, priority, department and application workflow status.
- Consequence: Issue #5 creates no dataset or ML result. Source licensing/consent, near-duplicate detection, agreement measurement, final split generation and minimum class support remain approval gates for later issues.

## D017 Configurable local backend port (2026-09-21, accepted)

- Decision: `BACKEND_PORT` controls both the local FastAPI launcher and Vite development proxy. It defaults to 8000 and must be an integer from 1 through 65535.
- Context: a stale host-level listener can occupy the default port and make the launcher attach the frontend to the wrong backend even when that process cannot be managed by its previously reported PID.
- Consequence: developers may select a free local port in the ignored `.env` without editing source or exposing credentials. Both services must be restarted after a port change; production deployment configuration is unchanged.

## D016 Raster map compatibility fallback (2026-09-21, accepted; provider default superseded by D028)

- Replace the Issue #4 MapLibre/OpenFreeMap renderer with lazy-loaded Leaflet and configurable raster tiles after the vector style and attribution loaded but the WebGL canvas remained blank in the actual in-app browser.
- Default the local academic demonstration to standard OpenStreetMap tiles with visible attribution. Permit only ordinary human interactive viewing: no prefetch, bulk download or offline mode. Keep `VITE_MAP_TILE_URL` configurable and choose a provider with a suitable SLA/terms before public deployment.
- Preserve the product behavior and component boundary: selecting a result opens the map; desktop click, marker drag, touch pan/zoom and reverse-geocoding continue to update the same location state.

Consequences: the live map now renders roads and buildings across the verified browser environment, the lazy map chunk is substantially smaller, and the public tile service remains best-effort rather than production infrastructure. D015's renderer choice is superseded; its geocoding, autocomplete and interaction decisions remain active.

## D015 Autocomplete search and detailed pin refinement (2026-09-20, accepted; renderer superseded by D016)

- Replace the one-shot-only citizen experience with debounced suggestions when the configured provider explicitly supports autocomplete. Keep a visible explicit-search fallback and never send typeahead traffic to public Nominatim.
- Select a backend MapTiler adapter for autocomplete and reverse geocoding. Keep its API key in ignored server environment configuration; expose only provider-neutral CivicAI contracts and capabilities to the browser.
- The original renderer choice was MapLibre with OpenFreeMap's Liberty style; D016 supersedes that renderer after live compatibility testing. The interaction decision remains: remove directional pin buttons, use desktop click, marker drag and touch interaction, and reverse-geocode the moved pin before confirmation.
- Add nullable selection-source and device-accuracy metadata through migration 0004. Preserve all existing rows and keep these fields outside the current classification experiment.

Consequences: the full autocomplete experience needs a user-supplied MapTiler key and restart; without one, the safe explicit-search fallback remains available. MapTiler receives search text/coordinates. The current tile-provider consequences are recorded in D016. No free public service is treated as a production SLA.

## D014 Issue #4 accessible issue-location selection (2026-09-20, accepted)

- Treat location as the issue location, which may differ from the reporter's current position.
- Offer explicit text search, current device location and optional map refinement. Search-result confirmation must not require map use.
- Require photo evidence and a confirmed location in the citizen frontend. Keep backend fields nullable for existing rows and API compatibility; this is a UI policy, not a retroactive database constraint.
- Store nullable `location_label`, `location_precision` (`exact`, `approximate`, `broad`) and `location_details` alongside coordinates. Never present a locality centroid as an exact surveyed point.
- Put geocoding behind a provider adapter and backend endpoint. Start with policy-compliant, rate-limited, cached, user-triggered Nominatim-compatible search; forbid typeahead against the public service and keep the provider configurable.
- Use an interactive map renderer only for optional refinement. Do not add navigation, continuous tracking, PostGIS or routing.

Consequences: migration 0003 is additive; the complaint response expands; public geocoding remains a local-demo dependency without a production SLA; frontend validation becomes stricter than the backward-compatible API.

## D013 Issue #3 photos and citizen location (2026-09-20, accepted)

- Keep optional coordinates in the backend for future geospatial capabilities; remove manual coordinate entry from citizen UX.
- Capture location only after a user action and browser permission. Failure or refusal does not block submission.
- Location is metadata only and is excluded from the current text/image/multimodal minor-project experiment.
- Use multipart creation with optional image_ref in PostgreSQL and local files in data/uploads/complaints (UPLOAD_DIR override). Never store blobs in PostgreSQL.
- JPEG/PNG only, 5 MiB input/output, 20 million pixels, generated UUID names, decoded-format validation and metadata-free re-encoding. Uploaded files are ignored by Git and served as raster content with nosniff.
- Local anonymous images are accessible to anyone who can reach the server. Production authentication, retention, malware scanning and orphan reconciliation remain future work.
- Video is deferred because storage, transcoding, moderation and ML processing exceed this issue.
- Browser location uses low-power accuracy, accepts a device fix up to five minutes old, and waits up to 30 seconds. This replaces the original fresh-only ten-second request, which caused avoidable timeouts after permission was granted on Windows. Provider failure still leaves location optional and gives device-settings guidance.


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
- Consequence: Issue #2 deferred authentication, images, maps, ML, classification, prioritization, routing, analytics and deployment. Issue #3 subsequently added optional images and browser location while preserving the MVP boundary documented in `MVP_SCOPE.md`; the other capabilities remain deferred.

## D012 Minimal frontend stack and local API proxy

- Date: 2026-09-20
- Status: accepted for Issue #2
- Decision: Use React 19, TypeScript, Vite and Vitest with Testing Library. Keep request code in a small API client and use Vite's local proxy for the existing `/api` and `/health` paths.
- Consequence: The MVP needs no router, component library, global state library or backend CORS change. Node.js 22.12 or newer is required. npm manages and locks frontend dependencies.
