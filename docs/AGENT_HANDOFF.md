# CivicAI engineering handoff

Latest implementation checkpoint, 2026-11-21: citizen complaint submission collects three bounded priority-context facts and atomically creates an anonymous `citizen_report` event through migration 0011. Full automated gates pass (547 backend/research; 60 frontend; production build). This is not deployed to the local Docker stack yet. Next use the backup-first ML demo launcher, submit one clearly labelled demo complaint through the citizen UI, and confirm its context/suggestion appears in the municipal panel without status mutation. Preserve the official 112 warning and the classification/priority separation; do not add image-severity claims.

Verified on 2026-10-17 from branch `main` at starting commit `cadb4c590be9ac5fcbc3e11e8fe75c71e58481e0`. This is the central onboarding map, not a replacement for the linked specifications. It records repository evidence, automated verification and explicitly identified human verification separately.

Research update, 2026-11-16: the user has redirected current work to assistant-led, India-only ML dataset acquisition across all civic domains, explicitly including non-road issues and West Bengal. Read the latest `CURRENT_STATE.md` entry and `research/INDIAN_CIVIC_COVERAGE.md` before relying on the older data-possession inventory below. New local image candidates exist, but no model/training approval or beta-validation claim has changed.

## START HERE — Fresh Codex Agent

Read, in order:

1. this file;
2. `AGENTS.md` and `docs/CURRENT_STATE.md`;
3. `docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md` and `docs/DECISIONS.md`;
4. `docs/API_CONTRACT.md` and the issue document relevant to the requested work;
5. `docs/DEVELOPMENT_WORKFLOW.md`, `docs/DEPLOYMENT.md` and `docs/OPERATIONS_RUNBOOK.md` before changing or deploying anything;
6. `docs/RESEARCH_PLAN.md`, `docs/DATA_SPECIFICATION.md` and `research/README.md` before touching research code or data.

First safe PowerShell commands from the repository root:

```powershell
git status --short --branch
git log -5 --oneline --decorate
git fetch --prune
git status --short --branch
git diff --check
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider --basetemp=.test-tmp\backend
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp=.test-tmp\research
Set-Location frontend
npm test
npm run build
```

Do not reset a database, remove Docker volumes, create a live-beta complaint, bootstrap an administrator, print environment files, or run ML training merely to establish a baseline. Inspect first. Ask before any destructive or live-data mutation.

Onboarding checklist:

- [ ] Working tree, branch, HEAD and `origin/main` are understood.
- [ ] The requested scope is mapped to an existing issue/document; no unrelated issue is started.
- [ ] Current code and tests have been inspected rather than relying on old prose.
- [ ] Environment files are ignored and secrets are not printed.
- [ ] Local and beta environments are not confused.
- [ ] Application data and research data remain separate.
- [ ] Any claim of “verified” states who/what verified it and in which environment.
- [ ] Research remains India-only and `training_approved=false` unless the documented human gate legitimately changes it.

## 1. Project identity and vision

CivicAI is the MCA project **“AI-Based Urban Civic Complaint Classification and Prioritization System.”** The implemented product is already useful without ML: citizens can report Indian civic issues with evidence and location, privately track them, optionally use an account, and municipal staff can process authorized work through an audited lifecycle. The research objective remains a controlled comparison of text-only, image-only, and text+image classification, with Macro-F1 as the primary metric. Classification (what the issue is) and prioritization (how urgent it is) are distinct concerns.

No classifier, prioritizer, ML inference path or defensible model result exists yet. Do not describe the current product as AI-enabled.

## 2. Verified current state

Status terms below have precise meanings:

- **VERIFIED IMPLEMENTED** — supported by current automated checks and/or the specifically recorded live human verification.
- **IMPLEMENTED BUT NOT RECENTLY VERIFIED** — present in code/tests, but not exercised in the current public beta audit.
- **PARTIAL** — a meaningful subset exists, with named gaps.
- **KNOWN ISSUE** — reproducible or evidenced limitation/defect.
- **PLANNED** — accepted future direction without implementation.
- **NOT IMPLEMENTED** — absent; do not imply otherwise.

### Citizen capabilities

| Capability | Status | Evidence and boundary |
|---|---|---|
| Anonymous complaint submission and text | VERIFIED IMPLEMENTED | Backend/API and frontend suites pass; owner reported successful public-beta submission. |
| JPEG/PNG image evidence | VERIFIED IMPLEMENTED | Sanitization, limits and storage adapters are tested; owner reported beta submission working. Citizen UI requires one image; API retains backward compatibility. |
| Location search, current location and map selection | VERIFIED IMPLEMENTED | Search/map/geolocation failure cases are tested; owner reported public-beta maps and submission working after MapTiler origin correction. |
| Geolocation permission/error handling | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Automated frontend tests cover denied, timeout, unavailable and unsupported cases; no current beta device matrix exists. |
| Private anonymous tracking | IMPLEMENTED BUT NOT RECENTLY VERIFIED | HMAC capability and privacy tests pass; Issue #12 has production-like human verification, but this audit did not use a live token. |
| Citizen registration | VERIFIED IMPLEMENTED | Identity tests pass; owner reported public-beta account creation working. |
| Email verification | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Single-use hashed token and Brevo adapter exist and are tested; current beta delivery/activation is not captured in repository feedback. |
| Email/password login | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Tested locally; current beta owner report does not distinguish this from Google sign-in. |
| Google OIDC login | VERIFIED IMPLEMENTED | State/nonce/issuer/audience logic is tested; owner reported public-beta “Continue with Google” working after exact redirect configuration. |
| Password reset and change | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Tested, but no current beta human record. |
| Citizen sessions and logout | IMPLEMENTED BUT NOT RECENTLY VERIFIED | PostgreSQL opaque-session behavior is tested and Issue #13 was production-like verified; not re-exercised in this beta audit. |
| My Complaints | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Account-scoped list/detail UI/API tests pass; no retained public-beta journey record. |
| Complaint ownership | VERIFIED IMPLEMENTED | Server-side ownership and privacy tests pass. |
| Anonymous complaint claiming | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Capability-based claim is tested; no current beta human record. |
| Citizen status/history presentation | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Sanitized history is tested; notifications are not implemented. |
| Responsive/mobile behavior | PARTIAL | Responsive/component tests and earlier Chromium checks exist. No broad beta device/browser study, screen-reader study or formal WCAG/GIGW conformance claim exists. |
| Error and empty states | VERIFIED IMPLEMENTED | Frontend suites exercise route, validation, provider, retry, empty and image failures. |

### Municipal capabilities

| Capability | Status | Evidence and boundary |
|---|---|---|
| First administrator bootstrap | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Interactive CLI is implemented/tested. The public beta's administrator provisioning was not confirmed in repository evidence during this handoff. |
| Staff invitation and activation | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Fixed-role/fixed-department, expiring invitation flow is tested and was production-like verified in Issue #13; current beta not recorded. |
| Staff authentication | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Tested; current public-beta municipal sign-in is not recorded as verified. |
| Roles and server-side permissions | VERIFIED IMPLEMENTED | Admin/operator dependencies and denial tests pass. |
| Department membership | VERIFIED IMPLEMENTED | Migration, constraints, UI/API and authorization tests pass. |
| Work queues and ownership/assignment | VERIFIED IMPLEMENTED | Permission-aware queue, assignment and history tests pass; Issue #11 has local browser/database verification. |
| Complaint claiming | VERIFIED IMPLEMENTED | Eligible operator self-claim and concurrency behavior are tested. |
| Lifecycle/status transitions | VERIFIED IMPLEMENTED | Controlled transitions, optimistic concurrency and history tests pass. |
| Internal notes | VERIFIED IMPLEMENTED | Stored only in municipal status events and excluded from citizen schemas; tests pass. |
| Immutable audit/history | VERIFIED IMPLEMENTED | Database immutability and application history tests pass. |
| Admin-only management | VERIFIED IMPLEMENTED | Department, membership, user and invitation controls are server-restricted and tested. |
| Operator restrictions | VERIFIED IMPLEMENTED | Cross-department, admin-route and evidence-access denials are tested. |
| Municipal dashboard | IMPLEMENTED BUT NOT RECENTLY VERIFIED | Dashboard/API tests pass; not re-exercised on current beta. |
| Map/evidence access | VERIFIED IMPLEMENTED | Authorized display and denial/missing-image tests pass. |
| Legacy route compatibility | VERIFIED IMPLEMENTED | `/admin` bookmarks normalize to the role-neutral `/municipal` surface; frontend tests pass. |

## 3. Technology stack

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL.
- React 19, TypeScript, Vite, Leaflet and MapTiler.
- pytest plus isolated PostgreSQL schemas; Vitest/Testing Library for the frontend.
- Argon2id passwords, opaque PostgreSQL-backed sessions and CSRF/origin enforcement.
- Local filesystem evidence in development; private S3-compatible Supabase Storage in beta.
- Capture/Mailpit/SMTP/Brevo email adapters by environment; Google OIDC server flow.
- Docker/Caddy/PostgreSQL for local production-like deployment; a single Render Docker web service for beta.

Dependencies use `pyproject.toml` and `frontend/package-lock.json`. There is no Python lock file; this remains technical debt.

## 4. Application architecture

The browser and API are same-origin in supported deployments. Citizen, municipal and research boundaries are intentional:

```text
Citizen React UI / Municipal React UI
                 |
          same-origin HTTPS
                 |
 FastAPI routes -> domain/services -> SQLAlchemy -> PostgreSQL
       |                  |
 authorized evidence     provider adapters
       |                  +-- MapTiler geocoding
 local/private S3         +-- capture/SMTP/Brevo email
                          +-- Google OIDC

 research/ + ignored data/ are offline and never imported by runtime services
```

Route handlers, schemas, service/domain logic and persistence are separated without microservices. `frontend/src/App.tsx` owns the citizen shell, `frontend/src/admin/AdminApp.tsx` the municipal workspace, and the map is lazy-loaded. `backend/src/civicai/main.py`, `routes.py` and `identity_routes.py` compose the HTTP surface. See `ARCHITECTURE.md` and `API_CONTRACT.md` for detail.

## 5. Citizen workflows

Anonymous reporting remains the baseline. The citizen supplies description, a valid photo and a confirmed issue location in the UI. The backend stores the complaint and returns a private tracking capability; there is no anonymous global feed. An optional verified citizen session binds new reports to the account. A capability holder may claim a previously anonymous complaint into the signed-in account.

Location may come from explicit MapTiler-backed search/autocomplete, current-device geolocation, or map adjustment. A location describes the issue, not necessarily the reporter. External provider failure preserves the draft. The UI requirement for image/location does not invalidate older records or the backward-compatible API.

Email/password signup is pending until a single-use verification link is consumed. Password reset uses a separate single-use token. Google creates a citizen identity only after validating issuer, audience, expiry, nonce and verified email. It does not grant municipal access and cannot automatically merge with an existing password account by matching email.

## 6. Municipal workflows

There is no privileged public signup. The first administrator is created with the interactive bootstrap CLI. Administrators invite subsequent staff with a fixed role and fixed department scope. Operators see department/individual work authorized by the backend; administrators see all work and manage staff, memberships and departments.

Assignment, self-claim and lifecycle mutations use optimistic concurrency and append immutable history. Internal notes and municipal identity are never serialized through citizen complaint schemas. Disabling a municipal user revokes active sessions. The final administrator, self-disable and self-demotion protections prevent accidental lockout.

## 7. Authentication and security model

Security invariants that must not be casually weakened:

- anonymous reporting and citizen self-registration remain possible;
- municipal privilege is invitation/bootstrap controlled—never inferred from Google, citizen signup or email;
- CivicAI owns authorization; PostgreSQL-backed opaque sessions are authoritative;
- only SHA-256 session/token digests are stored, with Argon2id for passwords;
- session cookies are HttpOnly and SameSite=Strict; beta/production require Secure; authenticated mutations require a session CSRF token and permitted Origin;
- Google issuer+subject is authoritative; unsafe email-only linking is prohibited and access/refresh tokens are not retained;
- citizen complaint reads are account- or capability-scoped; municipal reads are role/department scoped on the server;
- evidence is private and streamed through an authorized endpoint; Supabase buckets/object URLs are not public;
- internal notes, precise anonymous-only data and municipal history are protected;
- cloud credentials never enter frontend bundles. `VITE_MAPTILER_API_KEY` is the deliberate exception only in the sense that it is a browser-public provider key, not a secret; restrict it by allowed HTTP origin and quota;
- no wildcard credentialed CORS. Supported browser deployments are same-origin and the backend installs no permissive CORS middleware.

Important modules: `auth.py`, `citizen_auth.py`, `oidc.py`, `ownership.py`, `tracking.py`, `evidence.py`, `emailing.py`, `uploads.py`, `config.py`, `identity_routes.py` and `routes.py`. Important suites: `test_auth.py`, `test_identity.py`, `test_ownership.py`, `test_uploads.py`, `test_production_readiness.py`, `test_beta_adapters.py`, `test_api.py`, `test_admin_api.py`, `CitizenIdentity.test.tsx`, `App.test.tsx` and `AdminApp.test.tsx`.

## 8. Database and migrations

Alembic is authoritative; application startup does not create schema. Migrations are linear through `0011_citizen_priority_context.py`:

1. complaints;
2. image reference;
3. location context;
4. location quality metadata;
5. municipal lifecycle/history;
6. municipal auth/RBAC/audit;
7. departments, memberships, ownership and assignment history;
8. citizen identity, federated identity, tokens, invitation scope and shared sessions.
9. experimental text assessments and separate municipal reviews;
10. contextual-priority events and staff review history;
11. anonymous citizen priority-context attribution.

Apply migrations once before application startup. `Dockerfile.beta` runs `alembic upgrade head` before Uvicorn; production Compose uses a one-shot migration service. Never run concurrent migrations or reset a real database. Back up database and evidence together before destructive/schema work.

## 9. Local development setup

Windows/PowerShell is the primary documented workstation. Use Python 3.12, Node 22.12+ and separate PostgreSQL databases named with normal and `_test` roles as documented in `README.md`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
Copy-Item .env.example .env
# Populate the ignored .env, then create civicai and civicai_test in PostgreSQL.
.\.venv\Scripts\python.exe -m alembic upgrade head
Set-Location frontend
npm install
Set-Location ..
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

The app is `http://127.0.0.1:5173`; API is `http://127.0.0.1:8000` by default. Local uploads use `data/uploads/complaints`. `EMAIL_TRANSPORT=capture` writes ignored messages to `tmp/dev-mail`; never paste token-bearing contents into logs/issues. For a production-like local stack, use `.env.production`, `compose.production.yml` and the start/stop scripts. Add `compose.production.mailpit.yml` only for local verification; its inbox is loopback-only at `http://127.0.0.1:8025` and must never be deployed.

Google local callback: `http://127.0.0.1:5173/api/v1/citizen-auth/google/callback`. MapTiler local allowed origins require `localhost` and/or `127.0.0.1` as actually used by the browser.

## 10. Actual beta deployment

The public closed beta is `https://civicai-beta.onrender.com/`. The owner reported successful deployment and verified public account creation, Google login, complaint submission and maps. Earlier independent checks saw `/`, `/health` and `/ready` return 200 with release label `render-beta`. This handoff's attempted network recheck was blocked by the execution environment, so it does not upgrade those claims to a new 2026-10-17 live probe.

Actual architecture:

- one Render Free Singapore Docker web service built by `Dockerfile.beta`; React is compiled and served by FastAPI, so frontend and API share one HTTPS origin;
- migrations run before Uvicorn; Render health checks `/ready`; deploys follow passing GitHub checks on `main`;
- Supabase Free Mumbai PostgreSQL through the IPv4-compatible session pooler and a private S3-compatible Storage bucket;
- Brevo HTTPS transactional email (Render Free blocks outbound SMTP);
- Google OAuth web client with callback `https://civicai-beta.onrender.com/api/v1/citizen-auth/google/callback`;
- MapTiler for backend geocoding and browser tiles. The plan permits one key, so the same value is used in backend and frontend variables. Browser use makes it publicly observable; allowed origins include the exact beta hostname and local hosts as needed.

Secret/configuration variable **names**, never values, are catalogued in `.env.beta.example` and `render.yaml`. Critical names include `DATABASE_URL`, `PUBLIC_TRACKING_SECRET`, evidence S3 settings, `BREVO_API_KEY`, `MAPTILER_API_KEY`, `VITE_MAPTILER_API_KEY`, `MAPTILER_REQUEST_ORIGIN`, Google OIDC settings, `PUBLIC_BASE_URL` and `AUTH_ALLOWED_ORIGINS`. `.env.beta` is ignored and must remain untracked.

Free-tier limits: Render sleeps after inactivity and cold-start delay is expected; its filesystem is ephemeral. Supabase Free may pause and has bounded database/storage quotas. Brevo has a daily free-send limit. Database backups do not include Storage evidence; export and verify both separately. There is no HA, zero-downtime guarantee, formal RTO/RPO, automated evidence backup, central telemetry or production certification.

Redeploy by merging/pushing a fully verified `main` commit; `autoDeployTrigger: checksPass` gates Render. Confirm `/health`, `/ready`, migrations and browser journeys after wake/deploy. Bootstrap the first beta administrator interactively against the intended beta database without putting a password in environment files or shell history. At handoff time, repository evidence does not prove that this beta bootstrap was completed.

## 11. Testing and CI

Current 2026-10-17 local results:

- backend: **147 passed**, with three known dependency deprecation warnings;
- research: **56 passed**;
- frontend: **57 passed** (27 citizen shell, 23 municipal, 5 identity, 2 map);
- TypeScript: passed;
- Vite production build: passed;
- `pip check`: no broken requirements;
- OpenCity SHA-256: matched the pinned value;
- tracked environment audit: only placeholder examples tracked; `.env`, `.env.beta` and `.env.production` ignored.

The default sandbox temp directory was unwritable, so Python tests were rerun with workspace-local `--basetemp`. The full frontend invocation exceeded the command wrapper's 60-second ceiling after producing passing tests, so the four unchanged test files were run independently; all 57 passed. These are runner limitations, not application failures.

GitHub Actions `.github/workflows/quality.yml` installs the project, runs backend/research/frontend/type/build gates, performs dependency auditing, and builds production/beta containers. It does not automatically mutate databases or run live beta journeys.

## 12. Research and data integrity

Research is offline and independent of production complaint data. The current OpenCity/IChangeMyCity source is a Bengaluru text corpus of 16,071 rows with no images and no gold CivicAI labels. Its available raw file was re-hashed on 2026-10-17:

```text
d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac
```

`civicai-category-v1` remains proposed pending human approval. Source labels are retained separately and are not CivicAI truth. Audit/mapping outputs are proposals, not human annotations. Stage A generated blank, checksum-bound review forms; Stage B is paused awaiting genuine reviewers. `training_approved=false`. No model, final split, metric, experiment or novelty result exists.

Non-negotiable constraints: India-only provenance; no translated foreign substitution; documented licensing/provenance without invented approvals; privacy review/redaction; duplicate/event grouping before split; no train/evaluation leakage; no fabricated review; no random/synthetic image presented as paired evidence. A valid text/image comparison requires genuine aligned Indian records. Do not train or modify datasets without explicit, documented gate completion.

## 13. Known bugs, unresolved work and beta feedback

Repository-backed items:

| Severity | Status | Item |
|---|---|---|
| High if beta administration is needed | UNVERIFIED / operational | First beta administrator provisioning is not evidenced as completed. Verify active-admin count without exposing identities, then use the interactive bootstrap only when zero. |
| Medium | KNOWN LIMITATION | Render Free cold starts and Supabase free-project pausing can delay availability. |
| Medium | KNOWN LIMITATION | Database and private evidence require separate manual/off-site backup; no formal recovery guarantee exists. |
| Medium | PARTIAL | Mobile/accessibility work lacks a broad physical-device/browser/screen-reader study and is not formal WCAG/GIGW conformance. |
| Low | TECHNICAL DEBT | `RELEASE_ID` is configured as `render-beta`, not the deployed commit SHA, reducing runtime provenance. |
| Low | TECHNICAL DEBT | Login throttling is process-local; no distributed abuse-control layer exists. |
| Low | TECHNICAL DEBT | Python dependencies have ranges but no resolved lock; three upstream deprecation warnings remain. |
| Product gap | PLANNED | Citizen status notifications, richer communication, map visual polish and broader logged-in status UX are deferred. |
| Research blocker | PARTIAL | No approved labels and no genuine paired Indian text-image dataset; Stage B and ML remain paused. |

Resolved deployment incidents retained for context: Supabase pooler/URL configuration initially prevented startup; Google initially returned `redirect_uri_mismatch`; MapTiler origin formatting/geocoding caused 403/503 behavior; and an early Docker build exposed a Vite key in build-command output. Current code/config addresses these (exact URLs/origins, provider-specific adapters, and a non-interpolating build validation). Never reintroduce secret values into Docker `RUN` text or a public storage bucket.

`BETA_TEST_PROTOCOL.md` and `BETA_FEEDBACK_TEMPLATE.md` define safe testing/feedback capture, but the repository contains no populated tester-feedback ledger. Human reports held only in prior chat are not durable repository evidence. Sanitized reports—without passwords, session cookies, private tracking tokens, personal text/coordinates or private images—still need to be supplied and committed before they can be treated as the beta defect backlog.

## 14. Development and Git conventions

Work in small issue-scoped vertical slices. Inspect existing behavior, research edge cases from primary sources, implement narrowly, test failure/recovery paths, update truthful docs, inspect the diff, then commit/push a coherent increment. Never overwrite unrelated user changes. `main` is the currently used publication branch; fetch and compare before committing. The starting state for this handoff was clean and synchronized with `origin/main` at `cadb4c5`.

Do not commit environment files, credentials, uploads, private feedback, raw/derived datasets, model binaries or generated experiment artifacts. Use Alembic for schema changes. Preserve backward compatibility unless an explicit, documented migration decision says otherwise. Record consequential decisions in `DECISIONS.md` and execution evidence in `DEVELOPMENT_LOG.md`/the active issue document.

## 15. Critical decisions and “do not change casually” list

- Preserve anonymous reporting while keeping complaint tracking capability-private.
- Preserve same-origin browser architecture, server-side RBAC/department scoping and private evidence proxying.
- Preserve citizen/municipal identity separation and invitation-only municipal privilege.
- Preserve opaque database sessions, CSRF/origin checks, secure cookies and fail-closed production config.
- Do not expose backend/Supabase/Brevo/Google credentials to Vite. Treat only the MapTiler Vite key as deliberately public and origin-restricted.
- Do not make the evidence bucket public or return provider object URLs.
- Do not add ML inference before a versioned, reviewed, leakage-controlled research release exists.
- Do not mix workflow status, category and priority concepts.
- Do not silently “fix” historical data, labels or audit events.
- Do not claim formal production certification, all-India representativeness, accessibility conformance or model performance without evidence.

## 16. Immediate next step

Latest 2026-11-20: experimental 97-text AI-label model and guarded municipal assessment/review are implemented. Read `ML_DEMO.md`, `research/EXPLORATORY_BASELINE_RESULTS.md` and newest CURRENT_STATE. Owner confirmed Docker generation/acceptance/history after refresh; automated review checks pass. Do not repeat earlier preparation stages below. No independent accuracy, photo analysis or priority model claim. Next contextual-priority prototype; preserve staff control and explicit uncertainty.


Newest checkpoint (2026-11-19): `research/DEVELOPMENT_RELEASE.md` and `release.py` implement bound review packets and minimal redacted development exports. All 271 real pilot decisions remain pending in ignored `data/review/development-release-review-v1`; export was correctly refused. 277 research tests pass. Next complete substantive review/rights/privacy decisions or explicitly predeclare an AI weak-supervision experiment; do not invent human approvals. Real training remains disabled and the old pilot is not an untouched holdout. Earlier next-step entries below are historical.


Newest checkpoint (2026-11-19): `research/OFFLINE_BASELINE_RUNNER.md` describes the completed synthetic-only runner: 160 toy records/80 groups, three folds, six linear candidates plus dummy; 251 research tests pass. Optional research dependencies are installed locally and required by CI, not production. Real-data CLI inputs are always refused; no reviewed-release loader or real model evaluation exists. Next implement the reviewed-release contract and privacy-safe export with explicit provenance/rights/privacy/group/reference gates. Do not repeat the synthetic engine or infer approval from its tests.

Previous checkpoint: `research/BASELINE_READINESS.md` and `research/protocols/text_baseline_v1.json` complete readiness/protocol work. 157 AI candidates/156 containment components; four proposed development families cover 134 records/133 components. No approved labels/privacy/training release or untouched test set. Final ignored assessment is `baseline-readiness-v2`; 228 research tests pass. Next implement the offline baseline runner and test it on synthetic fixtures, with real-data execution gated on an explicit reviewed release. Do not repeat this assessment as model training; reference/privacy/rights tasks remain outstanding.

Previous checkpoint: `research/TEXT_ISSUE_ANNOTATION_REPORT.md` completed actual AI text review of all 271 pilot descriptions (190 described, 61 clarification, 16 scope, four unusable). Local artifacts are `issue-text-authored-v2` and `issue-text-validated-v2`; 366 components and 81 multi-component records. Do not redo transfer or this text pass. No independent labels/privacy clearance/training approval; context setting/time remain unknown and existing data/application are unchanged.

Previous checkpoint: `research/ISSUE_DESCRIPTION_DRAFT.md` describes the draft and 271-record transfer (139 provisional, 132 unresolved), now reviewed in the text pass above. Earlier recommendations below remain historical context.

Latest, 2026-11-18: read `research/CONTEXT_REVIEW_REPORT.md`. The assistant completed concrete recommendations for all 41 scope pairs, 134 flagged/no-span pilot records (97 retain context, 31 hold, six spans) and one duplicate candidate (future split-containment proposal, retain both, identity unknown). Cumulative privacy proposals: 43 spans in 37 records; no redaction/clearance. 162 research tests pass. Next encode and populate a versioned proposal-only family/asset/issue-kind annotation contract for the existing pilot. Do not redo the completed flag pass or infer human approval; 106 unflagged/no-span records were not reviewed here. Active taxonomy, source text/groups/splits and application are unchanged.

Previous follow-up: `research/CURATION_QA_REPORT.md` completes all-source-pair coverage and pilot duplicate/privacy proposal generation. Its 41 scope and 134 no-span flags were subsequently addressed in the recommendation pass above; three insufficient-source-label pairs remain unresolved. Neither pass supplies training labels or independent adjudication.

Completed earlier milestones: `research/AI_LABEL_PILOT_FINDINGS.md` holds AI proposals for all 271 tasks; `research/TAXONOMY_REVISION_PROPOSAL.md` defines the richer draft. Original human reviewer forms from `research/LABEL_PILOT.md` remain blank. Do not regenerate completed work or treat the assistant as an independent blinded reviewer.

The owner selected the research workstream. Use `ML_DECISION_SPEC.md`, `research/DATASET_AUDIT_2026_11_17.md` and `research/TEXT_CURATION_PROPOSAL.md` for the agreed task and release gates. Independent reference labels, rights/privacy review, full-corpus duplicate containment and actual class/language support remain prerequisites to a validated release. No human review, model readiness or all-India coverage may be invented; do not immediately train or implement a chatbot.

The earlier beta-validation backlog remains unresolved in repository evidence: municipal/admin and remaining identity journeys still need a sanitized result record. Do not claim the research checkpoint completed those journeys or mutate the live beta as part of dataset work.

## 17. Deeper references

- Product/current state: `PROJECT_CONTEXT.md`, `CURRENT_STATE.md`, `MVP_SCOPE.md`.
- Architecture/API/decisions: `ARCHITECTURE.md`, `API_CONTRACT.md`, `DECISIONS.md`.
- Identity and operations: `ISSUE_008_MUNICIPAL_OPERATIONS.md` through `ISSUE_013_MODERN_IDENTITY.md`.
- Beta/deployment: `ISSUE_014_CLOSED_BETA.md`, `DEPLOYMENT.md`, `OPERATIONS_RUNBOOK.md`, `BACKUP_RESTORE.md`.
- Research: `RESEARCH_PLAN.md`, `DATA_SPECIFICATION.md`, `ISSUE_005_RESEARCH_DATA_FOUNDATION.md`, `ISSUE_006_DATA_PREPARATION.md`, `ISSUE_007_HUMAN_REVIEW.md`, `research/README.md`, `research/SOURCE_REGISTER.md`, `research/ICMYC_DATASHEET.md`.
- Working method/history: `DEVELOPMENT_WORKFLOW.md`, `DEVELOPMENT_LOG.md`.
