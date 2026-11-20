# Current State

## 2026-11-20 — Assessment review regression checkpoint

Combined backend/research regression: **469 passed, three known deprecation warnings, 80.59s**. Added correction/deferral persistence, stale-input rejection, no-suggestion acceptance rejection, cross-complaint isolation and unchanged status/update timestamp checks. User Docker acceptance/persistence confirmation remains distinct from automated correction/deferral verification. TypeScript/Vite production build passed. Dataset checksum unchanged; private environment files/model ignored and untracked. No priority or photo analysis implemented. Next milestone: versioned contextual priority prototype with explicit reported facts and staff review, after publishing this experimental assessment checkpoint.


## 2026-11-20 — Owner verified Docker assessment and persistent review

Owner reports that Generate experimental assessment returned solid_waste, acceptance with an explanation appeared in review history, and that history remained after refreshing. This is human-reported verification of Docker inference plus review persistence, not direct agent browser inspection. Owner describes the attached photo as a trash can containing solid/semi-solid waste; the model currently consumes description text only, so this is not image classification evidence. The exact submitted description was not supplied in this confirmation; independent correctness is not established. Correction/defer journeys, unchanged-status browser check and broader model generalization remain separate checks. No production certification claimed.


## 2026-11-20 — Owner Docker demo startup confirmed healthy

Owner-supplied startup output confirms backup `backups/20261120-093046`, successful backend/migration/proxy image builds, healthy PostgreSQL, Mailpit, backend and proxy, completed migration/evidence-init containers and backend readiness HTTP 200. The corrected key-presence build step no longer expands the MapTiler value into the command. This is owner-run startup evidence, not agent-executed Docker inspection or authenticated end-to-end model verification. Next verify generation, correction/defer and persisted history in the Docker municipal browser; Linux model loading/inference is still unconfirmed until an assessment request succeeds. No public beta rollout or formal certification claimed.


## 2026-11-20 — Demo email startup root cause fixed in launcher

Owner logs show email_settings rejecting default capture in production. Local configuration inspection confirmed no production email transport/provider configured (no secrets printed). Launcher omitted the already-established Mailpit override; now includes `compose.production.mailpit.yml`. SMTP stays internal; inbox binds host loopback 8025. Base production settings and fail-closed guard unchanged. This is a launcher correction, not an ML/model/database failure. Owner Docker restart/health verification remains pending due to agent named-pipe access denial.

## 2026-11-20 — Owner Docker attempt: backup/build success, backend unhealthy

Owner supplied output confirms backup `backups/20261120-092357` and all three images built. Migration container exited; database healthy; backend unhealthy and proxy not started. Exit details/schema revision not yet independently checked. Backend cause cannot be determined from build output; requested container startup and health logs because agent Docker pipe access remains denied. Fixed proxy Dockerfile key-presence check to avoid expanded browser MapTiler value in future build logs (not yet rebuilt). No keys copied into documentation. No successful demo startup claimed.

## 2026-11-20 — Local Docker demo prepared, execution blocked

Added explicit optional research build argument, `compose.demo.yml` read-only model-file mount and `scripts/start-ml-demo.ps1` (localhost-only, artifact hash check, backup before rebuild, health wait). See `ML_DEMO.md`. Script syntax/diff checks passed. Docker Desktop named-pipe access was denied even after network permission; no Docker backup/rebuild/migration occurred. User-run script required, followed by actual health/browser verification. No model/data committed or baked into images.

## 2026-11-20 — Local demo activated; municipal sign-in needed

Verified local development target at schema 0008; created ignored pg_dump backup `backups/pre-assessment-2026-11-20.dump` (restore not tested), applied 0009 and confirmed revision by query. Set ignored `.env` experimental model path/hash without exposing credentials. Detached start-dev children did not remain reachable after launcher exit in this agent environment; started foreground tool sessions for backend 8001 and Vite 5173 instead. Browser now visibly loads municipal sign-in. No password reset, auth bypass, live-beta mutation or production deployment. Authenticated panel browser verification awaits owner sign-in; existing integration tests do not replace that check.

## 2026-11-20 — Broader integration regression

Full backend/research run: 463 passed, two failed because readiness and schema test still expected 0008. Updated both to 0009; focused schema/readiness rerun: 19 passed, three known warnings. Added unauthorized-operator tests. Frontend initial full run: 57 passed, one failed because assessment request was absent from existing mock; updated mock and rerun initiated. Browser at localhost:5173/admin returned connection refused; no visible workflow verification claimed. Updated outdated no-ML footer. Remaining: finish frontend rerun, start local app with migration/model configuration, browser verification, final diff/commit.

## 2026-11-20 — Real model generation and correction verification

Resumed after prior automatic approval review was unavailable due to usage limit; interrupted edits had not executed. Implemented category correction and review-history panel. TypeScript/Vite build passed. Five assessment API tests passed in 21.04s with three existing warnings, including the actual private local model (not skipped), persisted correction history, preserved original prediction, disabled configuration and invalid-hash failures. Added correction component test. No live browser verification, development model configuration, deployment or final full regression yet. Feature remains incomplete pending those checks and wider authorization/staleness coverage.

## 2026-11-19 — Assessment generation and panel draft

Added CSRF-protected generation and scoped review-history endpoints, operator-configured local model path plus SHA-256 verification before deserialization, and disabled-by-default behavior. Canonical guard now resides in backend; offline import retained. Municipal detail panel can request/list assessments and accept/defer with explanation. TypeScript and Vite production build passed. New endpoints/panel not yet integration/browser tested; correction and review-history display still absent from UI. No environment enabled, model redistributed, development migration or production rollout. Next test generation/failures/permissions, finish review UI and verify real browser workflow before declaring completion.

## 2026-11-19 — Assessment database verification unblocked

Connection failure was Windows network permission denial (10013), resolved by granting network access for this turn. Migration 0009 successfully applied through the isolated PostgreSQL test-schema fixture. Fixed new test submissions to use existing multipart API rather than JSON (415). `pytest backend/tests/test_assessments.py backend/tests/test_api.py -q --tb=short -p no:cacheprovider --basetemp tmp/pytest-assessment-verified`: **48 passed, 3 upstream deprecation warnings in 12.43s**. Verified empty list, anonymous rejection, seeded suggestion retrieval, review persistence with session-derived actor, unchanged complaint status and CSRF rejection. This is not full authorization/concurrency coverage. No development/production migration, model generation or UI activation. Next complete model generation, review-history read/UI and broader permission/staleness tests.

## 2026-11-19 — Assessment persistence/API draft (unverified)

Added migration 0009, assessment/review tables, municipal list/review endpoints using existing complaint access and CSRF dependencies. Reviews preserve original suggestions and do not mutate complaint workflow. Migration not applied to development/production. Backend database tests failed at fixture connection to the dedicated local test database; no passing persistence or permission claim. Syntax compilation passed. No model-generation endpoint or frontend added. Continue by restoring test-database connectivity, testing migration/persistence/scoping/staleness, then completing model generation and UI. Do not deploy this unfinished draft.

## 2026-11-19 — Municipal assessment contract started (integration incomplete)

Added strict internal `assessment_contract.py`: complaint/model/input identity, timestamp, experimental suggestion/review state and bounded reason codes. Review requests allow accept/correct/defer and reject caller-supplied actor identity or workflow-status fields. 13 focused contract tests passed in 0.94s. No migration, persistence, authorized endpoint or municipal UI is implemented by this checkpoint. The intended integration remains unfinished; next implement storage and authorization using existing complaint-access and CSRF patterns. No production behavior changed; no deployment or full regression claimed.

## 2026-11-19 — Offline guarded assessment

Implemented `research/civicai_research/assessment.py`; see `research/GUARDED_ASSESSMENT.md`. Six of seven authored probes deferred; supported drain example suggested with mandatory review. Heuristic scope checks are not validated OOD/language/negation detection. No API/UI integration or production activation. Next durable municipal assessment/review integration.

## 2026-11-19 — First real-text exploratory fit completed

See `research/EXPLORATORY_BASELINE_RESULTS.md`. 97 AI-screened Bengaluru texts, AI-proposed labels, grouped development comparison: selected mean macro-F1 0.8644 versus dummy 0.1434. No independent accuracy or deployment approval. Actual model/predictions remain ignored and local. Next inspect disagreements and harden the fixed experiment loader before application integration.

## 2026-11-19 — Minor presentation deadline now controls scope

Presentation is November 27. See `MINOR_PRESENTATION_PLAN.md`: prioritize an integrated experimental text-classification and contextual-priority workflow with municipal review; optional bounded AI assistance follows the core slice. Preserve real data-use/privacy gates, disclose AI-proposed training labels, and do not claim validated image severity or independent performance. No implementation or research approval is implied by this delivery plan. Next specify the bounded exploratory experiment and resolve source/privacy blockers.

## 2026-11-19 — Reviewed development export contract implemented

`research/DEVELOPMENT_RELEASE.md` documents the new source-bound review packet and redacted development exporter. Prepared all 271 pilot records at ignored `data/review/development-release-review-v1`, with pending record decisions and false review gates. The actual unreviewed export was refused, exit 1, with no output directory. No real dataset release or model training is claimed.

**277 research tests passed in 26.51s**, including 26 new tests for redaction, Unicode offsets, stale bindings, review gates, coverage, duplicate/group conflicts, minimal exports and failed writes. Original OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Runtime/application dependencies and behavior are unchanged; app tests/builds were not rerun. Real-data baseline execution still refuses every release.

Next complete substantive development review/rights/privacy decisions, preserving AI provenance and unresolved independent review. An assistant-only weak-supervision study needs a separately disclosed protocol, not invented human approvals. The contract is implemented; the review itself is not completed.


## 2026-11-19 — Offline baseline runner verified on synthetic fixtures

Implemented `research/civicai_research/text_baseline.py`; setup, artifacts and boundaries are documented in `research/OFFLINE_BASELINE_RUNNER.md`. Actual smoke run: 160 toy records, 80 artificial groups, four families, three grouped folds, six TF-IDF/logistic-regression candidates and a dummy comparator; 1,120 out-of-fold predictions. This verifies engineering only, not CivicAI accuracy. The selected synthetic model is ignored and is not connected to the application. Real-data CLI execution is always refused before reading input.

**251 research tests passed in 28.58s**, including 23 new engine/gate tests. Artifact hashes, ignored outputs and unchanged OpenCity checksum were verified. Optional pinned research dependencies and CI installation were added; base application dependencies, runtime and deployment are unchanged. Application tests/builds were not rerun. No real-data training, independent evaluation, severity model or production inference is complete.

Next implement the reviewed-release contract and privacy-safe export path. Independent reference labels, rights/privacy decisions and approved release remain unresolved; passing this synthetic test does not clear them. Preserve completed pilot/readiness work.

## 2026-11-18 — Baseline readiness and evaluation protocol completed

`research/BASELINE_READINESS.md` and `research/protocols/text_baseline_v1.json` specify the first proposed single-family text study. The read-only assessment finds 157 AI annotation candidates (156 conservative containment components), including 28 same-family multi-component reports. Deferred: 33 cross-family, 61 clarification, 16 scope, four unusable. No candidate is automatically training-eligible.

Roads/footpaths, solid waste, lighting and drainage meet the explicit development planning floor of 20 components/family: 134 records/133 components. This floor is an engineering choice, not statistical sufficiency or a restriction on CivicAI's wider reporting scope. Smaller families remain in the inventory. Candidate privacy flags: 21 span proposals, 16 context holds, 55 retention proposals and 65 without that contextual review. Independent reference, privacy and training-approved counts remain zero.

The protocol predeclares a dummy comparator, TF-IDF/logistic regression, grouped development validation, train-only preprocessing, macro/per-class metrics and a future fresh independently reviewed test set. The current pilot is development-only and cannot become an untouched final test. No model, split or performance result was produced. Final local output: ignored `data/review/baseline-readiness-v2`; **228 research tests passed in 21.58s**. Original data/application unchanged; no app suite/build rerun. Next implement the offline baseline runner with synthetic-fixture verification and an explicit real-data release gate, alongside unresolved reference/privacy/rights work.

## 2026-11-18 — Complete text-grounded richer pilot annotation

The assistant read and freshly annotated all 271 descriptions, including the 132 unresolved and 139 transferred records. `research/TEXT_ISSUE_ANNOTATION_REPORT.md` records 190 described-issue outcomes, 61 clarification cases, 16 scope-review cases and four unusable texts. There are 366 proposed components across 258 records, with multiple components in 81 records. Family/asset/kind tuples changed for 102 transferred records through refinement, additions or corrected assumptions; this is not a measured error rate.

Exact text evidence is bound by offsets/hashes; all reports remain AI proposals, not verified incidents or independent labels. Setting/time remain unknown in this pass. Privacy holds, source data, original proposals, active taxonomy, groups/splits and application behavior are unchanged. Final ignored artifacts: `data/review/issue-text-authored-v2` and `data/review/issue-text-validated-v2`; v1 is retained history.

**206 research tests passed in 20.23s** (33 new contract tests). Raw OpenCity hash remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. No application tests/builds rerun; no model trained or deployed. Next assess baseline readiness and predeclare evaluation using actual candidate/support counts, retaining independent-reference, rights/privacy and leakage-control gates. Do not redo the completed annotation pass.

## 2026-11-18 — Rich issue-description draft and pilot transfer

Implemented the first versioned family/asset/issue-kind draft in `research/civicai_research/issue_draft.py`; see `research/ISSUE_DESCRIPTION_DRAFT.md`. Applied existing proposals to all 271 pilot records: 139 records yield 153 provisional issue descriptions; 132 remain explicitly unresolved. Unknown setting/time/cause are preserved. This is a deterministic transfer, not fresh text annotation, a fully validated annotation schema or a training release. Original data, active taxonomy, privacy recommendations and application behavior are unchanged. Next directly annotate the unresolved texts and verify transferred descriptions against source evidence.


## 2026-11-18 — Contextual research recommendations completed

`research/CONTEXT_REVIEW_REPORT.md` records actual AI recommendations for all 41 scope-review source pairs (824 associated records), all 134 remaining flagged/no-span pilot texts, and the one near-text candidate. Scope: 30 pairs/512 records deferred from the initial physical-condition research target, four/33 conditional on public-asset evidence, four/269 requiring record context and three/10 specialist fire-safety review. These are proposals about a research target, not deletion, legal jurisdiction or exclusion from broad CivicAI reporting.

Privacy recommendations: 97 retain-context, 31 hold-for-context and six additional spans. Combined proposals now contain 43 spans in 37 records. No text was redacted and nothing is privacy-cleared. The 106 unflagged/no-span records were not reviewed in this contextual pass. Recommend future split containment for the near-text pair while retaining both; event identity remains unverified and existing groups/splits are unchanged.

Ignored authored/validated ledgers preserve input/text hashes and per-record rationales. The new validator refuses incomplete or inconsistent decisions, invalid offsets, false approvals and overwrites. **162 research tests passed in 21.26s**. Raw OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. No application/dependency/deployment changes; app suites/builds not rerun. Training, privacy and independent-review approvals remain false.

Next: implement and populate a versioned proposal-only family/asset/issue-kind annotation contract for the existing pilot. Preserve active taxonomy v1; no independent labels or release approval may be inferred. Rights, full-corpus privacy/duplicate checks and independent reference adjudication remain outstanding.

## 2026-11-17 — Full source-pair coverage and pilot QA proposals

`research/CURATION_QA_REPORT.md` records the completed coverage pass: all 231 source pairs/16,071 records accounted for by an explicit draft-family crosswalk. 187 pairs (14,883 records) have family proposals, 41 (824) need scope review, and three (364) remain source-label-ambiguous. Counts are source associations, not validated record labels or all-India coverage. Active taxonomy/mapping v1 is unchanged.

The 271-record pilot QA found one cross-group near-text candidate and generated 28 privacy spans in 23 records. Assistant inspection trimmed one overbroad span, retyped one and added nine missed spans: 37 proposed spans in 31 records; 134 AI-flagged records still lack spans. Original text/groups/forms are untouched. Nothing has been merged, physically redacted, independently adjudicated or approved for training.

Local outputs: ignored `data/review/curation-qa-v1` and `data/review/curation-qa-span-review-v1`. **135 research tests pass**; raw OpenCity hash remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. No app changes/tests/builds or deployment activity. Next resolve scope and record-level annotation rules plus contextual privacy/event decisions before adopting a taxonomy or training release; no human approvals inferred.

## 2026-11-17 — Complete AI pilot pass and taxonomy revision draft

All **271 pilot descriptions** have now been read and assigned explicitly AI-authored proposals: 125 provisional supported cases, 14 multiple-issue cases, 86 taxonomy/scope gaps and 46 unclear cases. Zero remain in this assistant pass; 165 contain proposed privacy-review concerns. These are not independent reference labels, privacy clearance or performance metrics. Read `research/AI_LABEL_PILOT_FINDINGS.md` and `research/TAXONOMY_REVISION_PROPOSAL.md`.

The new draft separates service family, asset and issue kind, preserving missing-service, private-property, mixed-issue and uncertain-source cases. It does not replace taxonomy v1 or reclassify application records. A concrete near-duplicate pair crosses current proposed groups, so no independent-incident or split-readiness claim is made.

Ignored `data/review/ai-pilot-complete-v1` combines the original 40 and new 231 responses with input provenance and hashes. `ai_labels` now supports disjoint batch combination and mandatory full-coverage checks, refuses overlaps/overwrite and never grants training approval. **120 research tests passed in 12.47s**; complete-pilot validation passes. Application suites/builds were not rerun for isolated research changes. Raw OpenCity hash was rechecked unchanged: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Human submissions remain zero; Stage B and training remain unapproved.

Next: source-pair coverage audit against the draft families, semantic duplicate and privacy-span proposals, then independent reference adjudication before taxonomy/release adoption. Do not repeat the completed 271-task AI pass or mistake its completion for release readiness.

## 2026-11-17 — First actual AI-assisted label proposal batch

Read `research/AI_LABEL_PILOT_FINDINGS.md`. The assistant read and proposed decisions for tasks 1–40 of the 271-task pilot: 16 supported named-category cases, one multiple-issue case, 19 taxonomy/scope gaps and four unclear cases. Privacy concerns were recorded for 22 records; no privacy clearance/redaction is claimed. There are **231 tasks remaining** in this pass. Proposals and rationales are retained locally under ignored `data/review/ai-pilot-batch-v1` with text/input hashes; no source text is committed.

The new structural validator rejects fabricated approval flags, unknown/duplicate tasks, changed input text and inconsistent categories. It cannot verify semantic truth. Human forms, raw data, taxonomy v1 and application behavior are unchanged; training remains unapproved. Next finish the remaining AI-assisted pilot batches and produce a versioned taxonomy recommendation before seeking independent reference review. Do not equate this assistant pass with human annotation or a completed pilot.

## 2026-11-17 — Source-label-blinded guideline pilot prepared

`research/LABEL_PILOT.md` documents the next label-quality step. The offline generator produced 271 blank reviewer tasks from 271 proposed containment groups in ignored `data/interim/label-pilot-v1`, with at most 20 per category/review-route stratum. Reviewer tasks hide source labels/proposals; a separate coordinator key preserves traceability. Selected input hashes and output hashes are recorded. This is a guideline pilot, not a representative evaluation holdout or an approved training release.

The guide defines ambiguous/multiple-issue, language and privacy decisions and concrete category boundaries. It records source-family evidence for broader taxonomy work (animals, pollution, traffic, trees and supply/service requests). Taxonomy v1 and Stage A forms remain unchanged. No independent responses exist; annotation agreement, privacy clearance, training and deployment remain unapproved. Next obtain genuine pilot responses/adjudication and revise supported definitions; any assistant-generated labels must be explicitly described as AI-assisted proposals.

Research regression: **104 passed in 9.01s**. No application changes or application-suite reruns. Raw OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac` as bound by the verified proposal; raw acquisition was not rerun.

## 2026-11-17 — Reproducible Bengaluru text-curation proposal

The new offline proposal command assesses the frozen 16,071-record OpenCity corpus with integrity checks, source-rule proposals, contact/URL masking candidates, complete duplicate-containment groups and explicit review routes. See `research/TEXT_CURATION_PROPOSAL.md` for reproducible commands, per-class support and remaining gates. Raw data, taxonomy, Stage A forms, application code and existing complaint behavior are unchanged.

Final output `data/processed/icmyc-text-proposal-v2` contains 7,289 candidate-review records and 8,782 targeted-review records, 264 contact/URL flags and 14 category-conflict groups. The smallest nonempty screened class is water leakage (53 records); `other` has no accepted mapping support. These are proposals, not verified labels, anonymized records or independent incidents. All labels remain null/pending, splits unassigned, approved records zero and `training_approved=false`. Human submissions remain absent; Stage B has not started.

Research regression: **98 passed**. Input/derived hashes are verified by the full-corpus run; OpenCity raw SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Application tests/builds were not rerun for this isolated research change. Next resolve mapping/taxonomy, privacy, independent-reference, duplicate/event, rights and split-support gates; no classifier, severity predictor or chatbot has been trained or deployed.

## 2026-11-17 — ML decision specification and targeted dataset audit completed

The agreed design is recorded in `ML_DECISION_SPEC.md`: broad Indian civic reporting, evaluated classification support, category-specific severity only when evidence/labels permit it, and a separate transparent contextual priority proposal with municipal review. Unknown/conflicting evidence is explicit and does not become low priority. Optional complaint clarification assistance is a later scoped feature; no AI provider, paid call or integration is configured.

`research/DATASET_AUDIT_2026_11_17.md` records 12 discovery queries, nine additional candidate dispositions and task-readiness gaps. New leads include a large multi-category image page with unverified Indian provenance, a synthetic multilingual civic seed set excluded from real-incident evaluation, request-only text/speech grievance research, and historical West Bengal inundation metadata for possible future context. No new incident dataset, reviewed label, taxonomy change or training release was created.

Local acquisition markers and hashes were rechecked, including all 62 Commons files and their null/unassigned labels, the DWSD archive and footpath metadata. The incomplete footpath archive remains excluded. OpenCity raw SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Existing research regression passes **83 tests**; application suites/builds were not rerun because this checkpoint changes documentation only.

Next scoped research work is the reproducible OpenCity text-curation proposal and label-support/readiness report, preserving real review/approval gates. Image-source and augmentation issues remain explicit. No model or all-India performance is claimed; the original paired-modality study remains conditional on genuine paired data. Existing application and beta-validation limitations below remain unchanged.

## 2026-11-16 — Broad Indian civic dataset acquisition

The user's current workstream is assistant-led Indian ML data collection across civic domains, including West Bengal, not a road-only detector. The application/deployment baseline below is unchanged. See `research/INDIAN_CIVIC_COVERAGE.md` for the full inventory, source links, rights, coverage gaps and severity design boundaries.

Acquired outside Git: DWSD West Bengal archive with 784 images and 784 matched masks (publisher SHA-256 verified); 62 distinct licensed Commons candidate photos across 13 retrieval topics (42 source-described West Bengal photos); Pune footpath metadata/license and 583 publisher severity labels. The footpath 4.5 GB image archive stalled after 55,574,528 bytes and was stopped, renamed `.zip.partial` and left `INCOMPLETE`; a separate metadata-only snapshot is complete. No transfer remains running. These sources are unpaired and not training-approved.

Added a bounded acquisition CLI and offline tests for download integrity, host/redirect/filename restrictions, no overwrite, incomplete status, licensing gates, metadata-only mode and preservation of pending labels. DWSD CRC/decode/pair checks pass; its paper's conflicting original-image/augmentation descriptions still prevent assuming 784 independent scenes or accepting its train/test split. Commons hashes are distinct across both snapshots; near-duplicate/privacy/location/label review remains. OpenCity raw SHA-256 is unchanged: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.

No model, metric, severity predictor or new application feature has been implemented. Stage B and the original proposed taxonomy remain unchanged. Next research work is source/scene/privacy curation and an explicitly versioned label-support plan, including genuine paired-data and severity-label gaps.

Final focused regression: **83 research tests pass** (56 existing + 27 acquisition cases). Backend/frontend/builds were not rerun for this research-only change; their last recorded evidence below remains historical.

## 2026-10-17 — Engineering handoff and deployed beta reality

The repository has a verified fresh-agent entry point at `docs/AGENT_HANDOFF.md`. The public closed beta is deployed at `https://civicai-beta.onrender.com/` using the Issue #14 Render/Supabase/Brevo/Google/MapTiler architecture. The owner reports that public account creation, Google sign-in, complaint submission and maps work. The repository does not yet contain durable evidence that the first beta administrator was provisioned or that the full municipal, staff-invitation, password-recovery and multi-user protocol was completed; those remain the immediate beta-validation task rather than a new product feature.

Current regression evidence is 147 backend tests, 56 unchanged research tests, 57 frontend tests, passing TypeScript and production build, and consistent Python dependencies. The OpenCity raw checksum remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`; Stage B is paused and `training_approved=false`. See `AGENT_HANDOFF.md` for the feature-by-feature status matrix, security boundaries, deployment facts, known gaps and onboarding order.

## Issue #13 — modern identity (implemented and live-verified)

CivicAI preserves anonymous reporting while adding self-service verified citizen accounts (email/password and Google OIDC architecture), secure recovery, server-owned complaint ownership, My Complaints, sanitized status history and capability-proven anonymous complaint claiming. Municipal access is presented through `/staff/sign-in` and role-neutral `/municipal`; administrators provision staff with fixed-role/fixed-department invitations. Existing municipal users, RBAC, memberships and histories remain intact through migration `0008`.

Automated state: 143 backend tests, 56 unchanged research tests, 57 frontend tests, TypeScript and the Vite production build pass. The owner completed real Google sign-in, callback, citizen-session persistence/profile/logout checks through the production-like HTTPS stack. A local-only Mailpit override then verified SMTP delivery, successful municipal invitation acceptance, operator sign-in, authorized queue access, admin-control hiding, direct admin-route denial and logout without weakening the normal production configuration. See `docs/ISSUE_013_MODERN_IDENTITY.md`.

## Issue #12 production tile defect fixed and human-verified

Production-like verification found that the compiled `tile.openstreetmap.org` default returned visible `Access blocked / 403` tiles. The rest of the production stack remains healthy. The narrow remediation replaces that unsupported production default with MapTiler Streets v4 through browser-public `VITE_MAPTILER_API_KEY`. Because the current MapTiler plan permits only one active key, Compose reuses `MAPTILER_API_KEY` when no frontend override is set; that shared value is publicly observable and must be origin/usage restricted. Separate frontend/backend values remain supported later. Compose also derives `MAPTILER_REQUEST_ORIGIN` from the site address so MapTiler continues to accept backend geocoding after the key is origin-restricted. The proxy build fails without either key value, Leaflet retains MapTiler/OpenStreetMap attribution, and Caddy permits only MapTiler's image origin. There is no silent anonymous fallback.

The owner configured `localhost` in MapTiler Allowed HTTP Origins and verified the rebuilt HTTPS production-like stack: location search still works, MapTiler tiles render without the earlier OSM 403 placeholders, complaint submission succeeds, and the complaint appears in the municipal workspace with no blocking browser issue. Ignored `.env.production` remains the only local credential source. No unrelated database or research/ML artifact changed.

## Issue #12 production readiness completed and human-verified

CivicAI now has a portable production package: Caddy is the only public service and serves the Vite production bundle/TLS before a private non-root FastAPI container; PostgreSQL is private; database, evidence and Caddy state use persistent named volumes; a one-shot Alembic service gates application startup. Production configuration fails closed for weak tracking secret, insecure cookie, non-HTTPS allowed origin and unsafe evidence path. Liveness reports a safe release ID; readiness checks PostgreSQL, exact migration `0007` and writable evidence storage without depending on geocoding.

The prior anonymous global complaint feed is intentionally disabled. New submissions return a private HMAC capability; capability status exposes only complaint UUID, description, status and timestamps. Exact location, labels, evidence, ownership and internal history are absent. Evidence now requires a municipal session and complaint-level server authorization. A dry-run consistency tool reports missing/orphan/invalid media without deleting.

Coordinated database/evidence backup, disposable restore verification, diagnostics, startup/shutdown runbooks, bounded container logs and GitHub Actions quality gates are implemented. Final verification passes 185 Python tests (129 backend and unchanged 56 research), all 52 frontend tests, TypeScript and the production build; Python dependency consistency and the production npm audit pass. Compose renders with example placeholders and uses PostgreSQL 18's correct `/var/lib/postgresql` persistent mount. A real native `pg_dump`/`pg_restore` recovery into disposable database `civicai_restore_issue12_20261002_195619` restored migration `0007`, all operational table classes and five hash-identical evidence files; the application media audit reported 5/5 consistent.

The live development browser submitted one clearly synthetic photo/location complaint, opened its private tracking link, displayed no image/location/internal activity, rejected a wrong capability with 404 and rejected anonymous evidence with 401. The owner then completed the production-like HTTPS verification through Caddy: Docker PostgreSQL/backend/proxy were healthy, administrator bootstrap/login and municipal features worked, a citizen complaint with searched/map location persisted into the intentionally fresh production database, and the complaint appeared on the administrative side. This is a verified project deployment checkpoint, not formal production certification, high-availability proof, or regulatory/security accreditation. No research artifact or ML state changed; the raw checksum was reverified as `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`, and Stage B remains paused.

## Issue #11 department ownership completed and live-verified

Migration `0007` adds administrator-managed active/inactive departments, many-to-many memberships, nullable current complaint department/assignee fields and immutable assignment/membership histories. Existing complaints remain safely unassigned. Administrator and operator visibility is enforced server-side: admins see/manage all ownership; operators see member-department or individually assigned work and may atomically self-claim eligible department work. Assignment is optimistic-concurrency protected, naturally idempotent for exact retries and transactional with its history event.

The municipal UI now exposes My work, department, assigned-to-me and admin unassigned/all queues; ownership on responsive cards/tables; detail assignment/self-claim/history; and department/membership administration. Unresolved work blocks department deactivation and membership removal. Disabled assignees remain visible and require explicit reassignment. Citizen resources contain no ownership details. Validated/generated request IDs and privacy-minimized structured request logs improve local correlation.

Final verification passes 177 Python tests (121 backend and 56 unchanged research), 27 citizen and 23 municipal frontend tests, TypeScript compilation and the production build. Development PostgreSQL is at migration `0007`. Real-browser checks covered department/operator setup, membership, assignment, permission-aware queues, operator self-claim, status progression, stale-write rejection with note preservation, a usable 390 × 844 CSS-pixel operator queue and session revocation; final browser warning/error logs were empty. Direct PostgreSQL inspection confirmed the current owner plus two assignment and three status events; anonymous API output contained no ownership fields. Both temporary accounts were disabled and their sessions revoked. The raw OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`; Issue #7 Stage B remains paused.

## Issue #10 product UX hardening implemented and live-verified

The anonymous citizen and authenticated municipal experiences now share a small token-based visual system, mobile-first reflow, strong focus treatment, skip links, semantic landmarks, route titles and truthful 404/error/empty/loading/success states. Citizen reporting has a four-step single-page hierarchy, photo preview, linked focusable error summary, accidental-unsent-draft warning and complete acknowledgement. The mobile municipal queue uses complaint cards rather than forcing the desktop table sideways; navigation is compact and keyboard-operable. Significant rejection/account changes use an accessible confirmation dialog. Existing complaint, evidence, lifecycle, authentication, RBAC and CSRF behavior is unchanged.

Municipal code is now route-lazy, reducing the local production initial JS entry from 259.24 kB (79.01 kB gzip) to 246.02 kB (76.31 kB gzip), with a 30.07 kB lazy admin chunk; the 150.70 kB lazy map chunk remains separate. Evidence images use native lazy loading, reserved dimensions and graceful failure copy. No dependency, backend endpoint or migration was added.

Verification passes 166 Python tests (110 backend, 56 unchanged research), 27 citizen tests and 20 municipal tests. TypeScript compilation and production build pass. Real Chromium checks covered effective widths from approximately 356 to 1,600 px plus narrow landscape with no citizen/admin horizontal page overflow. A synthetic photo/location complaint persisted, appeared in the responsive municipal queue and advanced to Under review with audited history. The temporary audit administrator was disabled and sessions revoked. The immutable OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`; Issue #7 Stage B remains paused.

## Issue #9 municipal authentication and RBAC implemented and live-verified

Migration `0006` is at development PostgreSQL head. Municipal operations now use PostgreSQL-backed opaque sessions with an HttpOnly, SameSite=Strict cookie, eight-hour absolute expiry, session-bound CSRF tokens for authenticated mutations, exact-Origin checks when an Origin is supplied, and Argon2id password hashes. There is no bearer token or password in browser storage and no application signing secret: random session tokens are stored only as SHA-256 digests. Production mode refuses `AUTH_COOKIE_SECURE=false`; CivicAI adds no CORS middleware because the supported browser topology is same-origin.

`municipal_operator` can use complaint operations; `municipal_admin` has those capabilities plus `/admin/users` account list/create/disable/reactivate/role controls. The backend enforces every role. Self-disable, self-demotion and removal of the final active admin are blocked. Disabled users cannot log in and their existing sessions are revoked. Successful login/logout and account changes create security audit events. New complaint status events store the authenticated actor through a nullable foreign key, while old truthful null actors remain unchanged. Citizen endpoints remain anonymous and never serialize internal notes, municipal users, sessions or password hashes.

Live verification used only `issue9.demo.*` accounts and a synthetic complaint. Unauthenticated `/admin` showed login; invalid login was generic; admin and operator login worked; refresh revalidated the server session; an authenticated status change stored the admin actor and internal note in PostgreSQL; operator account creation, backend 403 enforcement, disable/session rejection/reactivation, logout invalidation and anonymous citizen access all passed. The browser console contained no warning/error. A real-browser login exposed and drove a fix for non-UTC PostgreSQL cookie expiry; a regression test now covers the `+05:30` case. Both synthetic accounts were disabled and their sessions revoked after verification so the owner can run the interactive bootstrap with a private password.

Final regression passes 166 Python tests (110 backend, 56 unchanged research) with the same three dependency deprecations, plus 24 citizen and 15 municipal frontend tests. TypeScript compilation and the production build pass. The combined frontend launch hit the known Windows worker-start timeout after the citizen file passed; the municipal file then passed independently. The OpenCity raw SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Issue #7 Stage B remains paused; no research artifact, taxonomy decision, label, split, model or result changed.

## Issue #8 municipal operations implemented and live-verified

Migration 0005 is at development PostgreSQL head. CivicAI supports `submitted`, `under_review`, `in_progress`, `resolved` and `rejected` through documented transitions; same-state requests are idempotent and stale `updated_at` values fail with 409. Every existing/new complaint has append-only history beginning with `created`; PostgreSQL rejects history update/delete. Operator notes are internal, limited to 1,000 characters and have no fabricated actor.

The municipal routes `/admin`, `/admin/complaints` and `/admin/complaints/:id` provide real operational totals, server pagination (20 default/100 maximum), status/date/location/photo filters, escaped text/UUID search, evidence inspection, a read-only submitted-location map, status changes and history. The citizen queue shows friendly current statuses and never receives internal notes. Dashboard values are application counts—not ML results. Issue #9 has since closed the unauthenticated administrative-API blocker described by this earlier checkpoint.

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
# Issue #14 deployment preparation (in progress)

The verified Issue #13 application now has a locally tested closed-beta deployment path: a single Render Docker service serving React and FastAPI, configurable private Supabase S3 evidence storage, Brevo HTTPS transactional email, a closed-beta notice, and a discoverable tracking entry point. Local Docker/Caddy/PostgreSQL/Mailpit behavior remains supported.

External Supabase, Brevo, Render, Google-hostname, first-admin, and live multi-user verification are not complete. Issue #14 is therefore not complete and the project is not formally production-certified. See `docs/ISSUE_014_CLOSED_BETA.md` and `docs/BETA_TEST_PROTOCOL.md`.
