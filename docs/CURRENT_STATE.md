# Current State

## Issue #8 municipal operations implemented and live-verified

Migration 0005 is at development PostgreSQL head. CivicAI supports `submitted`, `under_review`, `in_progress`, `resolved` and `rejected` through documented transitions; same-state requests are idempotent and stale `updated_at` values fail with 409. Every existing/new complaint has append-only history beginning with `created`; PostgreSQL rejects history update/delete. Operator notes are internal, limited to 1,000 characters and have no fabricated actor.

The municipal routes `/admin`, `/admin/complaints` and `/admin/complaints/:id` provide real operational totals, server pagination (20 default/100 maximum), status/date/location/photo filters, escaped text/UUID search, evidence inspection, a read-only submitted-location map, status changes and history. The citizen queue shows friendly current statuses and never receives internal notes. Dashboard values are application counts—not ML results. Administrative APIs remain unauthenticated and are a public-deployment blocker.

Live verification used existing synthetic development complaint `ecd45acb-63d3-42bd-b295-c758ac17694b`: stored photo, location and map rendered; Submitted → Under review persisted with an Issue #8 note; history, combined search/status filtering, reload and citizen-visible status matched; browser console was clear. Direct PostgreSQL inspection confirmed the state, two events and note. Research data was not used or changed.

Final regression passes 153 Python tests (97 backend, 56 research) with the same three dependency deprecations, plus 24 citizen and 9 municipal frontend tests. TypeScript compilation and production build pass. The two frontend files were run independently after the known Windows Vitest worker-start timeout recurred in a combined run. The raw OpenCity checksum remains unchanged. Git publication status is recorded in the completion report/development log.

Issue #7 Stage B is intentionally paused pending real human reviewers. No taxonomy approval, research label, split, model or prediction exists.

## Issue #7 Stage A implemented — awaiting human review

Issue #7 remains pre-training. The ignored local package `data/interim/issue7-review-v5` is reproducibly bound to the verified OpenCity snapshot, audit v5, proposed taxonomy/mapping, review schema and generator code. It contains blank offline forms for 8 taxonomy items, 231 original category/subcategory mapping groups, 201 distinct phone/email privacy flags, 1,406 priority record reviews, 400 duplicate/template groups, one license decision and one final dataset-approval gate. No human decisions are present and `training_approved` remains false.

Review tooling validates pseudonymous reviewer metadata, timezone timestamps, allowed states, immutable context and decision-specific fields. It supports partial/resumable independent submissions, rejects duplicate reviewer decisions, preserves disagreements, and generates a separate adjudication form. Deterministic redaction operates only on derived text; complex identifiers require explicit spans. A fail-closed readiness report cannot approve training while required reviews, conflicts or methodology gates remain unresolved. Stage B and all model work are stopped pending real human input.

Final Python regression passes all 135 tests (79 backend and 56 research) with the same three recorded dependency deprecations. The generated package accepts a blank template as zero completed decisions, has no duplicate item IDs, and the raw CSV hash still matches Issue #6. Frontend code and dependencies did not change, so the previously verified 24-test/build checkpoint was not rerun. Exact reviewer commands and limitations are in `ISSUE_007_HUMAN_REVIEW.md`. No frontend, backend, API, database, raw snapshot, taxonomy decision, label, split or model result changed.

## Issue #6 in progress — Indian source acquired and audited

The application remains at the verified Issue #4 behavior; this checkpoint changes only research code and documentation. A verified OpenCity/IChangeMyCity Bengaluru text snapshot is now stored locally outside Git: 16,071 records, raw SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`, zero images, no omissions. The importer retains original bytes and publisher metadata, uses strict Windows-1252 decoding where required, preserves source labels separately, leaves all CivicAI labels null and all splits unassigned, and completes only after manifest-referenced file hashes pass.

The reproducible audit identifies 7,843 high-confidence source-label mapping proposals, 2,255 ambiguous cases, 5,955 needing review and 18 rejected missing-label records. It records missingness, time/coordinate coverage, class imbalance, duplicate/template risks, script buckets and privacy-pattern screening without committing complaint text. These are candidate counts—not human labels or research results. The proposed accepted-class maximum/minimum ratio is about 59.82, and no reliable `other` mapping exists. Human taxonomy/mapping review, privacy curation, annotation, duplicate grouping and explicit training approval are still required.

A bounded Kolkata/KMC and West Bengal search found official complaint forms and workflow references but no verified downloadable complaint-level dataset with stable version and clear reuse terms. This does not prove none exists. No usable Indian paired text-image source is possessed; the India subset of RDD2022 remains an unacquired road-image-only candidate. Foreign civic records are explicitly excluded from training and evaluation.

Final regression passes all 127 Python tests (79 backend and 48 research) with the same three recorded dependency deprecations. All 24 frontend tests pass; TypeScript compilation and the production build pass with the existing approximately 238 kB initial bundle and 151 kB lazy map chunk. The first concurrent frontend attempt timed out while starting its worker before loading tests; the conclusive isolated single-worker run passed. `ISSUE_006_DATA_PREPARATION.md` and `research/ICMYC_DATASHEET.md` contain the evidence and remaining gates. No model has been trained and no performance metric is claimed.

## Issue #5 research data foundation implemented and locally verified

Branch: main.

Issue #5 versions the proposed eight-category taxonomy as `civicai-category-v1` and adds annotation guidelines, a dataset datasheet template, a candidate-source register and a strict JSONL manifest validator. The proposal remains pending human approval after the source audit. The validator checks schema and annotation-state consistency, safe relative file references, SHA-256 form, unique record/source identities, group separation, and exact text/image checksum leakage across assigned splits. Optional file verification checks existence and hashes against an explicit restricted-data root.

The committed manifest example contains eight explicitly synthetic contract records—one per category—and is not research data. No source is approved, no real record is labeled, no dataset is downloaded, and no model, metric or research result is claimed. The focused research suite passes 9 tests and the sample validator reports eight valid unassigned records with no warnings or errors. Scope, sources, acceptance criteria and limitations are recorded in `ISSUE_005_RESEARCH_DATA_FOUNDATION.md` and `research/README.md`.

## Issue #4 implemented and locally verified

Issue #4 acceptance criteria and provider constraints are recorded in `ISSUE_004_LOCATION_SELECTION.md`. The implementation adds accessible issue-place search, current-location reuse, optional map refinement and truthful location precision. The citizen frontend requires a photo and confirmed location while the API/database remain compatible with existing optional records.

### Issue #4 backend checkpoint

Migrations 0003 and 0004 are applied to development PostgreSQL without changing old rows. They add nullable label, precision, nearby details, selection source and device accuracy. Complaint create/read/list expose the additions while remaining compatible with coordinate-only or location-free clients. `POST /api/v1/location-search` and `POST /api/v1/location-reverse` use a normalized provider-neutral contract; `GET /api/v1/location-capabilities` tells the frontend whether autocomplete is allowed. The Nominatim fallback enforces explicit search, upstream pacing, caching, country configuration and sanitized failures. The MapTiler adapter enables autocomplete only when its server-side key is configured.

### Issue #4 frontend checkpoint

The citizen form now requires a valid photo and a confirmed issue location. Users may search by place/PIN/street/landmark, choose a result, use their current location, add nearby details, and refine the point on a lazy-loaded Leaflet street map. MapTiler mode provides 350 ms debounced autocomplete; Nominatim mode retains a visible Search button. Desktop left-click, marker drag and touch pan/zoom replace the directional controls. A moved pin is reverse-geocoded when possible, and changing any point invalidates confirmation. Search, browser-position, reverse-geocoding and map-tile errors retain the rest of the form.

Frontend verification: TypeScript compilation passes, all 24 interaction tests pass and the production build succeeds. The initial JavaScript bundle is about 238 kB and the lazy Leaflet map chunk is about 151 kB. MapTiler was configured locally through the ignored `.env` and verified through the running frontend: searching for Baranagar returned eight typeahead results, selecting one opened a detailed Leaflet/OpenStreetMap street map, and clicking the map moved the pin and reverse-geocoded the adjusted point to a nearby road/address. No location was confirmed and no demonstration complaint was created during that check. The key remains local and uncommitted.

The complete Issue #4 citizen workflow is now live-verified with a clearly labeled synthetic complaint. The browser accepted the description and PNG evidence, searched and selected Baranagar, adjusted the map pin, reverse-geocoded the point, accepted nearby details, required explicit confirmation, submitted successfully and increased the queue from eight to nine. API and direct PostgreSQL checks matched complaint `ecd45acb-63d3-42bd-b295-c758ac17694b`, including submitted status, image reference, coordinates, exact precision, map source, location label/details and timestamps. The stored image endpoint returned HTTP 200 as `image/png`. The demonstration record remains in the local development database.

### Verified Issue #3 baseline

- Anonymous multipart complaint creation with optional JPEG/PNG evidence.
- Nullable image_ref added by migration 0002; original migration unchanged.
- Local images in data/uploads/complaints (UPLOAD_DIR override); bytes are not stored in PostgreSQL.
- Citizen form has optional photo selection/removal and one-shot browser geolocation, without manual coordinate fields.
- Location denial, unavailable browser, timeout and omission permit submission.
- Location acquisition accepts a device fix up to five minutes old and waits up to 30 seconds; timeout guidance distinguishes browser permission from device provider availability.
- Complaint list displays image evidence and friendly location confirmation.
- Coordinates remain metadata, excluded from the current minor-project classification experiment.
- No ML, category, priority, severity, accounts, routing, maps or video.

## Verification

The Issue #3 checkpoint originally verified migration 0002 with 42 backend and 15 frontend tests. Issue #4 has advanced development PostgreSQL to migration 0004. The final combined regression was rerun after the live end-to-end submission: 79 backend tests and 24 frontend tests passed; TypeScript compilation and the production build also passed; Alembic reports `0004 (head)`. Three existing dependency deprecations and the known pytest cache-permission warning remain non-blocking.

Local availability was rechecked after the frontend development process stopped and produced a browser “site can't be reached” error. The backend remained healthy. `scripts/start-dev.ps1` now checks and starts the missing local services and verifies the Vite complaint API proxy before reporting readiness. The site and proxied complaint list were reachable again after using it.

A host-level listener remained on the default backend port even though its earlier process ID was no longer addressable. Local `.env` now selects port 8001; the startup helper and Vite development proxy share `BACKEND_PORT`, while the tracked default stays 8000. Health, complaints, provider capabilities, MapTiler search and reverse lookup were all verified through the frontend proxy on port 5173.

Real browser: uploaded synthetic PNG, submitted without location, displayed image, submitted text after an actual location timeout, reloaded and confirmed both records remained. PostgreSQL confirmed the image reference and nullable coordinates. Browser console was clear.

Successful device location capture is now verified in the live browser. A complaint with optional photo and captured location was submitted; the UI shows it as location-provided, the API returns both coordinates, and the user independently confirmed the values in pgAdmin. Automated tests cover success, denial, timeout, unavailable API and late callbacks. An observed Windows registry consent value remained `Deny` even after capture succeeded, so it is not treated as authoritative for this desktop-browser flow; the browser API result is the operational check.

## References

API_CONTRACT.md describes multipart/search contracts and limits. ISSUE_003_EDGE_CASES.md and ISSUE_004_LOCATION_SELECTION.md record primary-source research and tradeoffs. DEVELOPMENT_LOG.md contains checkpoints. No production security, geocoding SLA, public deployment or research-results claim is made.
