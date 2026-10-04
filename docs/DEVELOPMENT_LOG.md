# Development Log

## 2026-10-03 — Issue #13 modern identity

Added migration `0008`, verified citizen email/password identity, recovery/change flows, Google OIDC server-flow architecture, account-scoped complaint ownership/history/claiming, shared opaque sessions, provider-agnostic email, invitation-based municipal provisioning, role-neutral municipal routes and responsive identity UI. Existing anonymous capabilities, municipal RBAC/departments and research artifacts remain unchanged. Automated gates: 143 backend, 56 unchanged research and 57 frontend tests plus TypeScript and the production build passed; real Google/provider and final production-like browser verification remain pending external configuration.

## 2026-10-03 — GitHub Actions package-install repair

The first `main` Quality Gates run failed before test execution because the workflow attempted `pip install -e ./research`, but `research/` is source within the repository rather than an independently packaged project and intentionally has no `pyproject.toml` or `setup.py`. The CI install step now installs the root project with its test extra only; pytest still discovers the unchanged research suite from the repository root. GitHub's container-build job had already passed, and no application, database, deployment or research behavior changed.

## 2026-10-03 — Issue #12 completed after production-like human verification

Final regression passed 185 Python tests (129 backend and unchanged 56 research) with the three known dependency deprecations plus the local pytest-cache ACL warning; 52 frontend tests; TypeScript compilation; and the Vite production build. The initial bundle remains 246.27 kB (76.35 kB gzip), contains MapTiler Streets v4 and contains no old OSM tile host. `git diff --check` and value-based secret scanning passed. `.env.production` is ignored and untracked, its PostgreSQL/tracking/MapTiler values occur zero times in the prospective commit, and `.env.production.example` contains placeholders/empty optional override only.

The owner rebuilt and started the production-like Docker stack and verified it through `https://localhost`: PostgreSQL, backend and Caddy were healthy; administrator bootstrap/login and municipal screens worked; the production database was intentionally fresh and separate from development; citizen submission, location search and MapTiler rendering worked; the created complaint appeared administratively; and no blocking browser issue remained. The one available MapTiler key is currently shared by backend geocoding and frontend tiles, is publicly observable because it enters the browser bundle, and is restricted to `localhost` for this verification. The configuration retains an optional separate frontend key for a future multi-key plan.

The OpenCity raw source was directly re-hashed as `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Issue #12 is complete as a portable single-host project deployment checkpoint, not as formal production certification. Citizen notifications, signed-in citizen history/status, map visual polish and broader communication UX remain deferred and were not implemented.

## 2026-10-02 — Issue #12 production readiness implementation checkpoint

Selected a bounded, primary-source-backed Caddy/FastAPI/PostgreSQL Compose topology. Added multi-stage production images, private fixed networking, one-shot migration gating, persistent database/evidence/certificate volumes, strict production configuration, release-aware liveness, dependency/schema/storage readiness, derived proxy/application security headers, request-size control and bounded logs. Vite remains development-only and research/data/secrets are excluded from the build.

Closed the production evidence exposure: anonymous global list is 404, private HMAC status links expose only UUID/description/status/timestamps, and evidence requires authenticated complaint-level municipal access. Added a read-only database/media consistency audit, coordinated backup, disposable restore verification, operations/deployment/rollback documentation and a non-deploying GitHub Actions quality gate.

Final code-level verification passes 185 Python tests (129 backend and unchanged 56 research), all 50 frontend tests, TypeScript compilation, the Vite production build, `pip check`, production-dependency `npm audit` with zero findings, PowerShell parsing, Compose rendering and `git diff --check`. The local global npm wrapper remains broken, so its actual installed npm CLI and repository-local test/build binaries were used. The managed default pytest temp/cache ACL remains inaccessible, so backend tests use a fresh workspace `--basetemp`; three existing dependency deprecations plus the cache warning remain non-blocking.

A real native PostgreSQL/evidence backup and restore succeeded into disposable database `civicai_restore_issue12_20261002_195619`: migration `0007`, 11 complaints, 5 municipal users, 1 department, 16 status events, 2 assignment events, 22 security events and five hash-identical evidence files were present; the restored application media audit was 5/5 consistent. Sandbox policy blocked destructive cleanup, so the clearly named disposable database and sibling `civicai-restore-verification-*` scratch directory remain for manual removal.

Live development-browser verification submitted a clearly synthetic image/location complaint, showed the protected-evidence receipt, opened a capability status page with no image/precise location/internal activity, returned 404 for a wrong capability and 401 for anonymous evidence. `/health` and `/ready` returned 200 with request IDs and application security headers. At this checkpoint the managed process could not access Docker; the owner subsequently completed the production-like verification recorded in the 2026-10-03 entry above.

## 2026-10-02 — Issue #11 department ownership completed

- Added migration `0007`, department/membership administration, current complaint ownership, immutable assignment/membership histories, permission-aware server queues, self-claim, concurrency and naturally idempotent retry behavior.
- Added municipal ownership UI, responsive queue metadata, assignment detail/history, department management and My work/workload counts. Added validated response request IDs and safe structured local request logs.
- Added edge-case coverage for duplicate/invalid/inactive departments, membership retry/removal constraints, cross-department and disabled-user assignment, exact retry, stale conflict, concurrent-style self-claim, operator RBAC, citizen privacy, transactional rollback, database event immutability and safe request IDs.
- Final verification passed 177 Python tests (121 backend and 56 unchanged research), 27 citizen frontend tests, 23 municipal frontend tests, TypeScript compilation and production build. The three known dependency deprecations remain non-blocking and unchanged.
- Development PostgreSQL reached `0007`. The real browser verified department/operator setup, membership, department assignment, operator queue visibility, self-claim, status progression, clear stale-write rejection while preserving the unsaved note and a usable 390 × 844 CSS-pixel operator queue; final browser warning/error logs were empty. Direct PostgreSQL inspection confirmed the current assignment with two assignment events and three status events; anonymous API output had no ownership fields. Both synthetic accounts were disabled and their sessions revoked after testing.
- The raw OpenCity CSV remained SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Issue #7 Stage B remains paused; no taxonomy, label, split, approval, model, routing recommendation, priority or result changed.
- Publication is pending: the verified working tree could not be committed because the Codex sandbox identity has an explicit Windows deny ACL on this repository's `.git` directory, so no remote state changed. The owner can run the documented `git add`, `git commit` and `git push origin main` commands in normal PowerShell.

## 2026-10-02 — Issue #10 professional UX hardening completed

Audited every citizen and municipal route in the live Chromium application before redesign, including narrow reflow, keyboard behavior, validation, image/map behavior, session/account states, failures and unknown routes. Reviewed GIGW 3.0, WCAG 2.2, GOV.UK, USWDS and web.dev guidance and recorded the bounded findings/adopted principles in `ISSUE_010_PRODUCT_UX_HARDENING.md`.

Added a token-based responsive visual foundation, citizen task sections, photo preview, accessible linked error summary, unsent-draft warning, richer acknowledgement, semantic statuses, skip links, document titles and citizen/admin 404 pages. Added a compact keyboard-operable municipal menu, narrow-screen complaint cards, filter-state feedback, clearer empty/failure/session/conflict states, accessible confirmations for consequential actions, lazy/reserved evidence media and route-level lazy loading of the admin workspace. No dependency, backend contract, database migration or research artifact changed.

Verification passed 27 citizen and 20 municipal tests, TypeScript compilation, production build, and all 166 Python tests with the same three dependency deprecations. The initial local JS entry decreased from 259.24 kB/79.01 kB gzip to 246.02 kB/76.31 kB gzip, with a new 30.07 kB/7.86 kB gzip lazy admin chunk and unchanged lazy map chunk. Real-browser checks covered effective widths from roughly 356–1,600 px plus narrow landscape without horizontal page overflow. Synthetic complaint `731ddc82-b3d4-4ffa-82b7-5ee381d30273` proved citizen photo/location submission, responsive admin discovery, evidence/map display and an audited Submitted → Under review change. Logout passed; the temporary Issue #10 administrator was disabled and sessions revoked. The OpenCity raw checksum remained `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac` and Issue #7 Stage B remains paused.

Publication remained pending: the Codex sandbox could not create the repository's `.git/index.lock` because of an OS deny ACL, and the sandboxed credential helper could not authorize a side-effect-free alternate-object push. GitHub `main` remained at synchronized baseline `6ce0f17`; no remote history changed. The completed working tree therefore requires the owner's normal PowerShell Git identity for add/commit/push.

## 2026-10-01 — Issue #9 municipal authentication and RBAC completed

Added migration `0006`, minimal municipal users/roles, Argon2id hashing, PostgreSQL opaque sessions, session-bound CSRF, generic/throttled login, real logout, account safeguards, security audit events and nullable complaint-history actor foreign keys. Added `/admin/login`, authenticated startup/refresh, role-aware navigation, sign-out and administrator account management. Citizen submission remains anonymous and citizen schemas remain separate from internal history/notes.

Security decisions follow OWASP password storage/session/CSRF/authentication/REST guidance and MDN cookie behavior; exact sources and tradeoffs are in `ISSUE_009_AUTH_RBAC.md`. The supported browser topology remains same-origin with no CORS middleware. Production startup requires Secure cookies. The bootstrap command is interactive and refuses an existing active administrator.

Automated verification passed 166 Python tests (110 backend, 56 unchanged research), 39 frontend tests (24 citizen, 15 municipal), TypeScript compilation and production build. The combined frontend launch hit the known Windows worker-start timeout after the citizen file passed; the municipal file then passed independently. Development PostgreSQL reached `0006`. Browser/PostgreSQL verification used only `issue9.demo.*` identities and one synthetic complaint; all required auth/RBAC/account/status/logout/anonymous checks passed and browser logs were clean. Browser testing found a real `Asia/Calcutta` cookie-expiry formatting defect; UTC normalization and a `+05:30` regression test fixed it. Both synthetic accounts were disabled and their sessions revoked after verification, leaving bootstrap available for the owner. The raw OpenCity checksum remained `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Issue #7 Stage B remains paused.

## 2026-09-29 — Issue #8 municipal operations

Researched official MoHUA Swachhata platform/engineer/state-admin material and Government of India CPGRAMS/2024 handling guidance. Adopted controlled workflow, truthful tracking, evidence/location detail, operational summaries, reasoned internal notes and reopening to review. Deferred feedback/appeal, staff identity, assignments, wards, SLAs and category/priority displays because CivicAI lacks the required identity/data/security contracts.

Added migration 0005, five-state transition rules, immutable history, note validation, atomic stale-update protection, paginated/filterable/escaped-search admin APIs and real aggregates. Added municipal React routes/screens, read-only evidence map, image/map/empty/error fallbacks, citizen-friendly statuses and an explicit unauthenticated warning. No ML/research code or data changed.

Focused checkpoint: 96 backend tests passed before the final immutability test; citizen frontend passed 24/24 and municipal frontend 9/9; TypeScript and production build passed. One combined Vitest attempt passed the municipal file but its second worker timed out before loading the citizen file; both files then passed independently. Global `npm` is broken because its roaming `npm-cli.js` is missing, so local project executables were used.

Development PostgreSQL reached `0005 (head)`. Live browser verification loaded nine stored complaints/real totals, displayed synthetic complaint `ecd45acb-63d3-42bd-b295-c758ac17694b` with photo/location/read-only map, persisted Submitted → Under review plus an internal Issue #8 note, displayed history, filtered by text/status, preserved the change across navigation and showed Under review in the citizen queue. Browser console was clear. Research remained separate and untouched.

Final regression passed 153 Python tests (97 backend, 56 research) with the same three dependency warnings, all 33 frontend tests in isolated conclusive runs, TypeScript and the production build. Direct PostgreSQL inspection confirmed two events and the stored note. The immutable OpenCity raw checksum remained `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`; whitespace diff checks passed apart from informational CRLF notices.

## 2026-09-27 — Issue #7 Stage A human-review infrastructure

Verified clean synchronized `main` at `fd0add0`; the Issue #6 snapshot/audit were reused without downloading or regenerating them. Added a versioned offline review schema, checksum-bound package generator, blank reviewer-friendly CSV forms, submission validation, independent-review merging, duplicate-review detection, explicit conflict/adjudication output, deterministic non-destructive redaction primitives and a fail-closed curation-readiness report. OWASP CSV Injection guidance informed quoting, formula-leading-field escaping and the Protected View warning; the documentation states that no spreadsheet mitigation is universal.

Generated ignored package `data/interim/issue7-review-v5`: taxonomy 8, mapping 231, privacy 201, priority record 1,406, duplicate/template 400, license 1 and dataset approval 1. A focused test exposed and fixed a collision between normalized-duplicate and template-duplicate item IDs by including detection kind in the identity. All decision fields are blank and training approval is false. The source snapshot remained immutable. Final regression passed all 135 Python tests (79 backend and 56 research) with the same three dependency deprecations; diff whitespace checks passed. Frontend code/dependencies did not change, so its existing 24-test/build checkpoint was not rerun. No product, database, model, label, taxonomy approval, split or research metric changed.

## 2026-09-27 — Issue #6 Indian source acquisition and audit checkpoint

Completed a checksum-pinned local acquisition of the OpenCity/Janaagraha IChangeMyCity Bengaluru complaints resource. The ignored snapshot contains 16,071/16,071 records with no importer omissions, strict Windows-1252-to-UTF-8 text conversion, original publisher artifacts, separate source labels and no images. The raw CSV SHA-256 is `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. An interrupted integrity pass was resumed without redownloading; every referenced text file/hash passed before the snapshot was marked complete.

Added deterministic auditing for missingness, text quality, script evidence, mixed date formats, coordinates, category/ward distributions, exact/normalized/template duplicates and privacy-pattern screening. Added explicit proposed mapping states rather than silently treating publisher routing labels as CivicAI truth. Audit v5 reports 7,843 accepted mapping proposals, 2,255 ambiguous, 5,955 needing review and 18 rejected; accepted-proposal class support ranges from 3,350 garbage/waste to 56 water leakage. Compact mapping, suspicious/language and duplicate review artifacts contain references rather than raw complaint text. All records remain pending and unassigned, and `training_approved` remains false.

A bounded official-source search found KMC complaint forms/workflow but no verified downloadable complaint-level Kolkata/West Bengal dataset with stable version and clear terms. No claim of nonexistence is made. Foreign observations are excluded. No Indian paired text-image source is possessed, no model was trained and no metric was generated.

The acquisition/audit tests cover strict decoding, host/license/schema changes, interrupted verification, tamper refusal, invalid mapping state, deterministic privacy-conscious review output and immutable audit directories. Final regression passed all 127 Python tests (79 backend and 48 research) with the same three dependency deprecations. TypeScript compilation and production build passed. A concurrent Vitest run timed out while starting its worker before loading tests; the conclusive isolated single-worker run passed all 24 frontend tests. Diff whitespace validation passed. No application behavior, dependency or database migration changed.

## 2026-09-27 — Issue #6 preparation checkpoint; acquisition still open

Reviewed official NYC311 field changes, RDD2022 authors, TACO authors, the AWS IChangeMyCity registry, CESAMARD authors and scikit-learn evaluation guidance. Recorded source-specific suitability gaps in `ISSUE_006_DATA_PREPARATION.md`. No suitable paired eight-category source was approved or acquired. Category-derived text, generated descriptions and arbitrary same-category text/image pairing are excluded from the primary experiment. Source/category confounding must be audited.

Implemented local manifest ingestion with file integrity/content checks, immutable output publication, deterministic transitive event/duplicate components, conflicting-label quarantine, paired eligibility and support reports. Reports include code/data/taxonomy hashes and runtime versions. All outputs remain review proposals. Added regression coverage for malformed Issue #5 enum/category values that previously raised an unhandled TypeError.

Verification: 112 Python tests passed (79 backend plus 33 research), including reproducibility, row-order invariance, transitive duplicates, decoded-pixel duplicates, missing modalities, conflicting/disputed labels, pending/excluded records, corruption/missing files, immutable releases, mixed dataset versions and command-line output validation. Tests use synthetic fixtures only. Three known dependency deprecations remain; pytest cache was disabled and a fresh workspace temporary directory used. Diff whitespace checks passed. No frontend/API/database changes; no frontend rerun, model training, actual acquisition or final research split is claimed. Issue #6 remains in progress pending the real-data route.

## 2026-09-27 — Issue #5 research data foundation

Started the ML/research track at its defensible boundary rather than training on unverified data. Reviewed the official Indian Swachhata category/workflow material, NYC311 data evolution, Datasheets for Datasets, the NIST AI RMF Playbook and scikit-learn group-aware split guidance. Recorded exactly what is adopted and what remains unapproved in `ISSUE_005_RESEARCH_DATA_FOUNDATION.md` and the research source register.

Added `civicai-category-v1` with eight machine-readable categories and explicit boundaries; human rules for multi-issue complaints, `other`, emergencies, modality conflicts, privacy quarantine and adjudication; a dataset datasheet template; and a strict JSONL manifest contract. The dependency-free validator reports counts and rejects schema drift, inconsistent annotation states, unsafe paths, invalid checksums, duplicate record/source identities, group leakage and exact text/image hash leakage. Optional data-root verification checks referenced files and hashes without downloading anything.

The first focused pytest run encountered the already-known inaccessible Windows default temp directory: one non-`tmp_path` test passed and eight fixtures could not set up. Rerunning with a workspace-local `--basetemp` passed all 9 research tests. The eight-record synthetic contract manifest then validated with all categories present, all records unassigned, and zero errors/warnings. These are illustrative contract records, not observations or research results.

Final regression passed all 88 Python tests (79 existing backend tests plus 9 research tests), all 24 frontend tests, TypeScript compilation and the production build. The first frontend attempt timed out while starting a Vitest worker before loading any test; the conclusive single-worker run passed all tests. Python output contains the same three recorded dependency deprecations plus the known non-blocking pytest cache-permission warning. No Issue #4 application behavior or database migration changed.

## 2026-09-21 — Issue #4 full workflow accepted locally

Completed the final real-browser demonstration using only synthetic test content. The citizen flow accepted a required PNG, searched Baranagar with MapTiler autocomplete, selected a result, rendered the Leaflet/OpenStreetMap map, adjusted the pin, reverse-geocoded it, recorded nearby details, required explicit location confirmation and submitted the complaint. The live queue increased from eight to nine and displayed complaint prefix `ecd45acb` with its photo, confirmed address and details.

The API returned the full UUID `ecd45acb-63d3-42bd-b295-c758ac17694b`. A direct PostgreSQL query matched that UUID and verified submitted status, persisted image reference, non-null coordinates, location label, exact precision, map source, nearby details and both timestamps. The image endpoint returned HTTP 200 with `image/png` and 7,211 bytes. The record remains as clearly labeled local demonstration data.

Final regression after submission: 79 backend tests passed, 24 frontend tests passed, TypeScript compilation and the production build passed, and Alembic reported migration `0004 (head)`. Output contained the same three recorded dependency deprecations plus the known non-blocking pytest cache-permission warning. No GitHub push was attempted; publication remains the user's step after review.

## 2026-09-21 — MapTiler activation and local port recovery

The user configured the MapTiler key in the ignored root `.env`; no credential was printed, documented or staged. A stale host-level listener still occupied port 8000, and attempting to stop its obsolete PID correctly reported that no such process existed. Added a validated `BACKEND_PORT` setting shared by `scripts/start-dev.ps1` and Vite's API proxy. The tracked default remains 8000, while this machine uses 8001 in its ignored `.env`.

After restarting the intended backend with network access, the live frontend reported autocomplete and reverse-geocoding capabilities enabled. Searching for Baranagar produced eight MapTiler suggestions. Selecting the first result rendered a non-blank Leaflet/OpenStreetMap street map with roads, labels, zoom controls, attribution and a draggable marker. Clicking the map adjusted the pin and successfully reverse-geocoded it to a nearby road/address. No location was confirmed and no complaint was submitted. Frontend proxy health and complaint access remained successful.

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

## 2026-10-03 — Issue #13 identity verification checkpoint

Issue #13 adds separate citizen and municipal identity populations, email/password citizen accounts, Google authorization-code OIDC, account-scoped complaints, anonymous complaint claiming, role-neutral municipal routes and administrator-controlled staff invitations. Migration `0008` is at development head. The final automated regression passes 143 backend tests with the same three dependency deprecations, 56 unchanged research tests and 57 frontend tests; TypeScript and the Vite production build pass.

The owner verified the real Google flow through the production-like HTTPS stack: authorization returned to My Complaints, CivicAI established its opaque server-side session, refresh preserved it, Profile reported Google connection and logout ended it. Google-created identity remains citizen-only by architecture and tests.

The provider-cancellation callback was also exercised in a browser. It returned to citizen sign-in with the generic Google failure message and exposed no authorization code, provider detail or token.

Staff invitation testing exposed two environment defects rather than an authorization defect: a stale development backend lacked the new route, and automated test capture had polluted `tmp/dev-mail` with tokens belonging to isolated test schemas. The backend was restarted; test mail now uses per-test temporary directories; and a focused identity rerun passed 14 tests without changing the developer inbox count. A separate `compose.production.mailpit.yml` local verification override now routes production-like SMTP to a loopback-only Mailpit web inbox while keeping SMTP private. The normal production Compose contains no debug inbox and still rejects capture mode. The owner then successfully received and accepted a fresh invitation against the same production-like database.

The activated operator signed in through the role-neutral staff entry, loaded the permitted dashboard and complaint queue, had no staff/department administration navigation, was denied at the direct staff-management route and successfully logged out. This completes the live municipal authorization-boundary check.

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
# 2026-10-02 — Issue #12 production MapTiler tile remediation

Production-like HTTPS verification exposed a real, isolated defect: the frontend image had compiled `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, and the browser rendered the provider's `Access blocked / 403` tiles. The fix does not spoof or bypass OSM policy. Leaflet now uses MapTiler Streets v4 through browser-public `VITE_MAPTILER_API_KEY`. The current one-key plan reuses `MAPTILER_API_KEY` through a Compose fallback, so that value is publicly observable and protected through MapTiler origin/usage restrictions; a separate frontend override remains supported later. `MAPTILER_REQUEST_ORIGIN` identifies the same CivicAI site on backend geocoding requests so the origin restriction does not break search. The production proxy build fails closed without either key value, Caddy CSP permits `api.maptiler.com` images, and there is no anonymous fallback. MapTiler and OpenStreetMap attribution remain visible.

Focused code verification passes: 7/7 geocoding tests (including the new shared-key Origin header assertion), 2/2 tile-configuration tests, the unchanged 27 citizen and 23 municipal frontend tests, TypeScript compilation, and the Vite production build. Compose renders successfully, resolves the one-key fallback without a frontend override, and Caddy's CSP contains the MapTiler image origin but not the old OSM tile host. The built frontend contains MapTiler Streets v4 and no `tile.openstreetmap.org` reference. `git diff --check` passes. The browser-used key is restricted in MapTiler to Allowed HTTP Origin `localhost`; its existing value remains only in ignored `.env.production`.

The owner subsequently rebuilt the backend/proxy from normal PowerShell and verified production location search plus visible MapTiler rendering through `https://localhost`; the old 403 tile placeholders and blocking browser issue were gone. No real key was printed or committed, and no unrelated database, research, or ML behavior changed.
# 2026-10-04 — Issue #14 Phase A

Researched current official Render, Supabase, Brevo, and Google constraints. Added the single-service beta image/Blueprint, private evidence-storage abstraction, Supabase S3 adapter, Brevo HTTPS adapter, deployed-environment validation, low database pool limits, SPA fallback, beta CSP, closed-beta banner, tracking lookup entry point, beta configuration template, test protocol, and feedback template. Local regression results and the external provisioning gate are recorded in `docs/ISSUE_014_CLOSED_BETA.md`. No hosted service has yet been provisioned or claimed as verified.

Phase A verification passed 147 backend tests, 56 unchanged research tests, 57 frontend tests, TypeScript, the beta-configured Vite production build, dependency consistency, and whitespace checks. The OpenCity checksum remained `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Local Docker image execution was blocked only by the Codex sandbox's Docker named-pipe permission; CI now contains the equivalent beta-image build gate.

After Supabase and Brevo configuration, the Render template was clarified to require `MAPTILER_REQUEST_ORIGIN` alongside the browser build key. Both must be bound to the exact generated Render origin because the current MapTiler plan uses one origin-restricted key for frontend tiles and backend geocoding.
