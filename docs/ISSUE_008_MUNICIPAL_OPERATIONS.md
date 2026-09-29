# Issue #8 — Municipal operations dashboard and complaint lifecycle

Status: **implemented and locally verified**.

Issue #7 Stage B remains paused for human reviewers. Issue #8 changes only the product application and development database. It does not label research records, alter the OpenCity snapshot, train a model, or create predictions.

## Scope

The existing React application now contains:

- `/admin` — real stored operational totals;
- `/admin/complaints` — newest-first, server-paginated complaint queue with search and filters;
- `/admin/complaints/{complaint_id}` — evidence, submitted location, read-only map, status workflow and immutable history.

Citizen create/read/list contracts remain compatible. The citizen queue renders friendly labels for the truthful operational status. Internal operator notes are absent from citizen complaint resources.

## Lifecycle

`duplicate` is deliberately **not** a status. Later duplicate detection needs a relation/group that preserves lifecycle and evidence; forcing it into status would lose that distinction.

| Current | Permitted next state |
|---|---|
| `submitted` | `under_review`, `rejected` |
| `under_review` | `in_progress`, `rejected` |
| `in_progress` | `under_review`, `resolved`, `rejected` |
| `resolved` | `under_review` (reopen) |
| `rejected` | `under_review` (restore) |

Repeating the current status is idempotent: no timestamp or history row changes. Unsupported transitions return `409 invalid_status_transition`. Updates require the current `updated_at`; a stale screen returns `409 stale_complaint_update` before changing anything.

Every complaint has a `created` history row. Status changes append `status_changed` rows with previous/new status, UTC time, optional trimmed internal note (1–1,000 characters), and nullable `actor_id`. No operator identity is invented. PostgreSQL rejects update/delete of history rows.

## Listing, search and statistics

Admin listing uses one-based pages, defaults to 20 rows, caps pages at 100, and orders by `(created_at DESC, complaint_id DESC)`. Filters cover status, inclusive UTC date range, photo presence and coordinate-pair presence. Search supports exact UUID plus escaped case-insensitive description, location-label and nearby-detail matching. `%`, `_` and `\` remain literals. PostgreSQL indexes support newest-first and status/newest-first access; substring search stays simple at current academic scale.

Dashboard counts come from stored application complaints: total, each lifecycle state, last-seven-day submissions, photo presence and location presence. They are not ML results, priorities, categories, SLAs or department-performance claims.

## Evidence and map

The detail view reuses the lazy Leaflet/OpenStreetMap renderer in read-only mode. Operator interaction cannot alter the submitted point. Location label/context are primary; coordinates are secondary technical details. Missing coordinates and missing/failed images have explicit fallbacks without hiding the rest of the record.

## Official Indian references and adoption

- [MoHUA Swachhata](https://dashboard.swachh.city/) describes municipal forwarding, regular status updates, citizen feedback and post-resolution verification. CivicAI adopts evidence/location inspection and truthful lifecycle visibility; notifications/feedback are deferred.
- The official [Swachhata engineer manual](https://www.swachh.city/assets/files/User-Manual.pdf) documents operator status handling and reopening. CivicAI allows resolved/rejected complaints to return to review; citizen-triggered reopening awaits identity and authorization.
- The official [Swachhata state-admin FAQ](https://www.swachh.city/assets/files/Swachhata_State_Admin_Module_FAQ_V2.1.pdf) shows summaries, list/map views, filters and evidence detail. CivicAI adopts real summaries, list/status filters and an individual evidence map; it omits ward/category/SLA/engineer data that does not exist.
- [CPGRAMS](https://pgportal.gov.in/) provides unique tracking, status visibility, feedback and appeal. CivicAI preserves UUID tracking/current status; appeals and satisfaction feedback remain future authenticated work.
- The 2024 [CPGRAMS handling guidelines](https://www.pgportal.gov.in/Home/Preview/Q29tcHJlaGVuc2l2ZUd1aWRlbGluZXNGb3JIYW5kbGluZ1RoZVB1YmxpY0dyaWV2YW5jZXMucGRm) require reasoned handling and address wrong assignment/multi-issue grievances. CivicAI permits internal notes but invents no departments, routing or SLA.

These references informed bounded decisions; CivicAI does not claim equivalent production security, staffing or scale.

## API and database

Migration `0005` expands status, creates `complaint_status_events`, backfills creation events for existing complaints, adds query/history indexes and installs the immutability trigger. Original evidence/location fields are unchanged.

New endpoints:

- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/complaints`
- `GET /api/v1/admin/complaints/{complaint_id}`
- `GET /api/v1/admin/complaints/{complaint_id}/history`
- `PATCH /api/v1/admin/complaints/{complaint_id}/status`

## Security boundary

There is **no administrative authentication or authorization**. The UI states this prominently. Admin reads/mutations are for the local academic prototype only and are a public-deployment blocker. A fake login was not added. Internal notes and images are accessible to anyone who can reach the local server.

## Live verification

On 2026-09-29 migration `0005` reached PostgreSQL head. The browser loaded nine development complaints and real totals; displayed stored photo/location/map for synthetic complaint `ecd45acb-63d3-42bd-b295-c758ac17694b`; changed it from `submitted` to `under_review`; persisted note `Issue #8 live verification: municipal review started`; displayed history; found it through combined text/status filtering; and showed `under review` in the citizen queue. Browser console warnings/errors were empty. The demonstration record was already synthetic and is separate from research data.

## Deferred

Authentication/roles, operator assignment, departments, public updates, appeals/feedback, corrected-location evidence, duplicate relations, marker clustering, notifications, SLAs and all ML outputs remain separate milestones. A geographic overview was not added: nine complaints do not justify clustering, and the reusable detail map meets current operational need without rendering many heavy maps.

## Verification

- 153 Python tests passed: 97 backend and 56 research, with the same three dependency deprecation warnings.
- 33 frontend tests passed: 24 citizen and 9 municipal, run as two isolated files after the known Windows worker-start issue recurred in a combined run.
- TypeScript compilation and the production Vite build passed (about 252 kB initial JavaScript and 151 kB lazy map chunk).
- Migration `0005` is at development head; direct PostgreSQL inspection confirmed `under_review`, two history events and the exact Issue #8 note for the live synthetic record.
- The raw OpenCity CSV remains SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- `git diff --check` passed apart from informational Windows line-ending notices.
