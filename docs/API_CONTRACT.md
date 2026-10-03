# API Contract

## Issue #13 citizen identity and staff provisioning

Citizen identity: `POST /api/v1/citizen-auth/sign-up`, `/verify-email`, `/resend-verification`, `/login`, `/logout`, `/forgot-password`, `/reset-password`, `/change-password`; `GET /api/v1/citizen-auth/me`; and Google start/callback under `/api/v1/citizen-auth/google/*`. Google start/callback is redirect based and action-token values are never returned.

Owned complaints: `GET /api/v1/citizen/complaints` is server-paginated and session-scoped; `GET /api/v1/citizen/complaints/{id}` returns an owned record plus sanitized status history; `POST /api/v1/citizen/complaints/{id}/claim` requires citizen CSRF plus the valid Issue #12 capability in `{token}`. Authenticated ordinary submission links ownership from the cookie session; no account ID is accepted.

Staff provisioning: administrators use `GET|POST /api/v1/admin/staff-invitations` and `POST /api/v1/admin/staff-invitations/{id}/revoke`; invitees use `POST /api/v1/staff/accept-invite`. Public callers never choose role/departments. Existing municipal session and admin API contracts remain compatible.

Issue #3 changed POST /api/v1/complaints to multipart/form-data. Issue #4 adds optional location context and selection quality to that compatible multipart contract, plus provider-neutral search/reverse/capability endpoints. JSON complaint creation still returns 415. Issue #12 deliberately replaces anonymous list/detail/evidence reads with a private status capability and municipal-only evidence access.

## Submission

Multipart fields: description (required trimmed nonempty text), latitude (optional number -90..90), longitude (optional number -180..180), image (optional JPEG/PNG file), location_label (optional nonempty string, 300 characters), location_precision (optional `exact`, `approximate` or `broad`), location_details (optional nonempty string, 500 characters), location_source (optional `search`, `device` or `map`) and location_accuracy_m (optional finite number 0..100000). Omit unavailable coordinates. If any location-context field is sent, both coordinates plus label and precision are required. Accuracy is accepted only with source `device`. Coordinate-only legacy clients remain valid. Duplicate, unknown and server-owned fields are rejected. Do not set the Content-Type header manually in browser code; FormData supplies the boundary.

POST returns 201 with complaint_id, description, latitude, longitude, location_label, location_precision, location_details, location_source, location_accuracy_m, status, created_at, updated_at and a 64-character `tracking_token`. `image_ref` is always null in this anonymous response even when evidence was stored. New complaints start as `submitted`; UUID and UTC timestamps remain server-owned. The tracking token is shown only on submission, is a bearer capability and must not be logged or published.

The citizen Issue #4 frontend requires a photo and confirmed location. The API intentionally keeps both optional for existing records, compatibility and non-browser clients; frontend policy must not be described as a database invariant.

## Issue-location search

`GET /api/v1/location-capabilities` returns `{ "autocomplete": boolean, "reverse_geocoding": true }`. The frontend enables 350 ms debounced typeahead only when autocomplete is true and otherwise keeps explicit Search/Enter behavior.

`POST /api/v1/location-search` accepts JSON `{ "query": "Baranagar Municipality" }`. Query is trimmed, must contain 3–200 characters and rejects extra fields. It is used for both explicit search and, only with a capable configured provider, autocomplete.

Success returns up to five normalized results with provider_id, label, latitude, longitude and precision (`approximate` or `broad`). Search providers never return `exact`; only a user-confirmed device position or adjusted map pin receives that UI category. An empty array means no match. Provider timeout/failure returns 503 with code `location_search_unavailable` and a sanitized retry message.

`POST /api/v1/location-reverse` accepts latitude and longitude using the same coordinate bounds. It returns one normalized result or null when no label is available. Provider timeout/failure uses the same sanitized 503 behavior; the frontend retains the moved coordinates when label refresh fails.

The Nominatim fallback is country-restricted through configuration, limited to one upstream request per second and cached in memory for 15 minutes; it never advertises autocomplete. The MapTiler adapter advertises autocomplete and supports optional configured proximity bias. Provider keys stay server-side. Providers receive public-place search text or selected coordinates; users should not enter private information. No search query or coordinates are intentionally written to CivicAI application logs.

## Citizen reads and evidence

- `GET /api/v1/complaints` is intentionally disabled and returns 404. There is no anonymous enumeration feed.
- `GET /api/v1/complaints/{complaint_id}?tracking_token=<capability>` returns only `complaint_id`, description, status and created/updated timestamps. Missing, malformed or wrong capabilities return 404 to avoid existence disclosure. Coordinates, location labels/details, image references, ownership and internal history are excluded.
- `GET /api/v1/complaint-images/{filename}` requires a valid municipal session and complaint-level permission. Unauthenticated callers receive 401; authenticated but unauthorized callers receive 403; authorized missing files receive 404. Successful evidence uses its explicit raster MIME and `Cache-Control: private, no-store`.
- `GET /health` returns `{"status":"ok","release":"<safe-release-id>"}` without dependency checks.
- `GET /ready` returns 200 only when PostgreSQL responds, Alembic is exactly at `0008`, and evidence storage is writable; otherwise sanitized 503 JSON is returned.
- `/docs` and `/openapi.json` describe the multipart endpoint.

## Municipal operations

Issue #11 extends municipal resources only. Issue #12's capability status response never includes department, assignee, membership, workload or assignment history.

`GET /api/v1/admin/complaints` additionally accepts `department_id`, `assignee_user_id`, `assignment_state=assigned|unassigned`, and `queue=unassigned|mine|my_departments_unassigned`. The organization-wide `unassigned` queue is administrator-only. Operators receive only current member-department complaints or complaints individually assigned to them. Existing pagination and filters compose server-side.

Municipal list/detail items add safe department/assignee summaries. Detail adds chronological immutable `assignment_history`. `PATCH /api/v1/admin/complaints/{id}/assignment` is administrator-only and accepts nullable `department_id`, nullable `assignee_user_id`, timezone-aware `expected_updated_at`, and optional 1–1,000 character reason. Assignee requires an active member of the active selected department. An exact desired-state retry is idempotent; different stale state returns `409 stale_complaint_update`.

`POST /api/v1/admin/complaints/{id}/claim` accepts timezone-aware `expected_updated_at`. An active operator can claim only an unassigned complaint owned by a current member department. Concurrent claims use conditional update; one wins and stale competitors receive 409. `GET /api/v1/admin/work-summary` returns truthful personal/department queue counts, never performance or priority scores.

Department administration uses `GET|POST /api/v1/admin/departments`, `PATCH /api/v1/admin/departments/{id}`, `POST /api/v1/admin/departments/{id}/members`, and `DELETE /api/v1/admin/departments/{id}/members/{user_id}`. Mutations require admin plus CSRF. Slugs are stable; deactivation and membership removal fail with 409 while unresolved work would be stranded.

Every response contains `X-Request-ID`. Safe caller IDs match 8–64 ASCII letters/digits/dot/underscore/hyphen; invalid/missing values are replaced by server-generated UUID hex.

Every `/api/v1/admin/*` route requires a valid active municipal session. Complaint operations accept `municipal_operator` and `municipal_admin`; account routes require `municipal_admin`. Missing, expired, revoked or disabled-user sessions return 401. Insufficient role returns 403. The backend is authoritative regardless of visible frontend controls.

`GET /api/v1/admin/complaints` returns `{items,page,page_size,total,total_pages}`. Query parameters:

- `page` (default 1, minimum 1) and `page_size` (default 20, range 1–100);
- `status`: `submitted`, `under_review`, `in_progress`, `resolved` or `rejected`;
- `created_from`, `created_to`: inclusive timezone-aware timestamps; from must not exceed to;
- `has_location`, `has_photo`: booleans;
- `q`: at most 200 characters; blank means no search. Exact UUID plus literal escaped substring matching applies.

Results are deterministic newest-first by creation timestamp then UUID. A page beyond the result returns an empty `items` array with truthful totals.

`GET /api/v1/admin/complaints/{complaint_id}` returns the complaint plus chronological `history`. `GET /api/v1/admin/complaints/{complaint_id}/history` returns history alone. Events contain event/complaint IDs, event type, previous/new status, optional internal operator note, nullable actor ID and UTC occurrence time.

`PATCH /api/v1/admin/complaints/{complaint_id}/status` accepts:

```json
{
  "new_status": "under_review",
  "expected_updated_at": "2026-09-29T15:30:00Z",
  "operator_note": "Site inspection requested"
}
```

`expected_updated_at` must include a timezone. Note is optional trimmed text of 1–1,000 characters. Same-state requests return the unchanged complaint without adding history. Invalid transitions and stale screens return 409 with `invalid_status_transition` or `stale_complaint_update`. Missing/invalid IDs retain 404/422 behavior.

Status mutations require `X-CSRF-Token` from the current auth response. New history events contain the authenticated actor UUID. Existing pre-authentication events remain null. History and operator notes are never included by citizen list/detail responses.

`GET /api/v1/admin/dashboard` returns real stored totals for all complaints, each status, submissions in the last seven days, photo presence and location presence. It contains no ML or SLA metrics.

## Municipal authentication and accounts

- `POST /api/v1/auth/login` accepts `{username,password}`. Valid active credentials set the opaque HttpOnly session cookie and return `{user,csrf_token,expires_at}`. Unknown username, wrong password and disabled account share generic 401 wording. Repeated failures are throttled per normalized username and client IP with generic 429.
- `GET /api/v1/auth/me` verifies the database session and current active user, then returns the same public session shape. It is the frontend startup/refresh authority.
- `POST /api/v1/auth/logout` requires the session-bound `X-CSRF-Token`, revokes the database session, deletes the cookie and returns 204.
- `GET /api/v1/admin/users` lists safe account fields for administrators only.
- `POST /api/v1/admin/users` creates an operator or administrator from `{username,password,role}` and requires CSRF. Usernames normalize to lowercase and allow 3–64 letters, digits, dots, underscores or hyphens. Passwords require 12–128 characters and are returned only as Argon2id hashes internally—never through the API.
- `PATCH /api/v1/admin/users/{user_id}` accepts at least one of `role` or `is_active`; it requires administrator plus CSRF. Self-disable, self-demotion and removal of the final active administrator return 409. Disabling revokes that user's live sessions.

The cookie is host-only, path `/`, HttpOnly and SameSite=Strict. It is Secure when `AUTH_COOKIE_SECURE=true`; production startup requires that setting. The default absolute lifetime is eight hours (configurable from 1–24). CivicAI intentionally exposes no credentialed cross-origin CORS policy; local Vite requests are same-origin through its proxy. Auth/admin responses use `Cache-Control: no-store`; API responses also include nosniff, frame-denial and no-referrer headers.

## Errors and limits

Errors use code/message, with details for field-validation errors. Invalid fields/images return 422, oversized uploads 413, wrong request media type 415, missing resources 404, lifecycle/concurrency conflicts 409, and database unavailability 503.

Images: 5 MiB input and re-encoded output; 20 million pixels; single frame only. Total multipart body: 5 MiB + 256 KiB. Non-file multipart parts: 64 KiB. One image maximum. MIME must match decoded JPEG/PNG format. Files are re-encoded without source metadata, preserving orientation. Original filenames are ignored. Storage unavailability returns 503.

Citizen complaint creation remains anonymous. Status retrieval requires the per-complaint capability returned at creation. Complaint-image retrieval and municipal operations require authentication and server-side authorization; account administration additionally requires `municipal_admin`. Never expose evidence through a static directory or public object URL.
