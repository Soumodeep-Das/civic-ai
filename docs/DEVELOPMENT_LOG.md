# Development Log

## November 24 municipal queue update

The municipal queue shows category and priority from current staff reviews. Filters apply to the authorized result set before returning the requested page. Pending review includes complaints with either decision outstanding, deferred or stale. Accepted and corrected values are visible on desktop and mobile. Review panels distinguish confirmed writes with failed history refreshes from uncertain network outcomes.

Local checks passed 547 Python tests (three warnings), 60 existing frontend tests, the added confirmed-save regression and the TypeScript/Vite production build. Docker Desktop denied engine access during verification. The rebuilt HTTPS browser journey is pending. Filtered reads scan authorized complaints in batches and have not been load-tested.

## 2026-11-22 — Documentation audit and reader-facing overhaul

Reviewed GitHub and the local implementation, rebuilt the README and architecture, added a documentation index and major-project roadmap, and corrected stale research/API/identity/deployment claims. Public-clone model limitations, AI-label metrics, the CI artifact-test skip and the distinction between original synopsis and delivered scope are explicit. Historical files and reference attachments are retained. No application or research data changed. See [review findings](DOCUMENTATION_REVIEW_2026_11_22.md).

## 2026-11-21 — Presentation readiness gate

Synchronized clean `main` at `1980a80`; [GitHub Quality gates run 44879439546](https://github.com/Soumodeep-Das/civic-ai/actions/runs/44879439546) passed both `test` and `container-build` jobs. Successful steps include PostgreSQL service initialization, migration, full Python/frontend tests, dependency check/audit, production build, Compose validation and production/beta container builds. Local results: research 312 passed; database-independent backend 82 passed with two known upstream warnings; frontend 60 passed; `pip check` and TypeScript/Vite production build passed. The local full backend suite was stopped after setup errors because ignored `.env` correctly points to dedicated `civic-ai_test` but connection attempts to `127.0.0.1:5432` failed under sandbox restrictions; the service state was not established; no normal database was substituted. Local npm audit could not resolve the npm registry, while CI's equivalent audit passed.

Direct OpenCity SHA-256 recheck matched `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. `.env`, `.env.production`, `.env.beta`, uploads and temporary outputs remain ignored/untracked. Key/private-key pattern scans found no candidate; PostgreSQL URL pattern hits were limited to tracked example/CI/Compose/restore-script files and were not treated as secrets. Whitespace/status checks were clean.

Live read-only verification showed the existing authenticated municipal complaint with protected image, rendered MapTiler map, citizen context and persisted accepted priority; status remained Submitted, browser console warnings/errors were empty and 390 × 844 had no page-level horizontal overflow. A fresh in-app reload was blocked by the expected untrusted localhost certificate and was not bypassed. HTTPS probes passed health/readiness and the public-directory, wrong-capability and anonymous-municipal denial cases. Added `MINOR_DEMO_RUNBOOK.md`; no feature, dependency, schema, credential or application data changed.

## 2026-11-21 — Bounded photo-assistance decision

Reviewed the current protected evidence path and official documentation for Google Cloud Vision, Hugging Face zero-shot image classification/CLIP, OpenAI API data controls and FixMyStreet's evidence workflow. Deliberately added no provider, credential, runtime dependency, model or API call. Generic labels are not validated civic defect/severity evidence; CivicAI lacks an approved representative Indian image release, independent photo labels and the required external-processing disclosure/consent, budget and failure boundary. `PHOTO_ASSISTANCE_DECISION.md` records the decision and major-project re-entry gates. This prose-only checkpoint changes no application behavior; `git diff --check` is the verification gate. Next run full regression and freeze the existing demonstrable workflow.

## 2026-11-20 — Assessment review regression checkpoint

Frontend regression: **58 passed across five files in 76.06s**. Combined backend/research regression: **469 passed, three known deprecation warnings, 80.59s**. Added correction/deferral persistence, stale-input rejection, no-suggestion acceptance rejection, cross-complaint isolation and unchanged status/update timestamp checks. User Docker acceptance/persistence confirmation remains distinct from automated correction/deferral verification. TypeScript/Vite production build passed. Dataset checksum unchanged; private environment files/model ignored and untracked. No priority or photo analysis implemented. Next milestone: versioned contextual priority prototype with explicit reported facts and staff review, after publishing this experimental assessment checkpoint.


## 2026-11-20 — Owner verified Docker assessment and persistent review

Owner reports that Generate experimental assessment returned solid_waste, acceptance with an explanation appeared in review history, and that history remained after refreshing. This is human-reported verification of Docker inference plus review persistence, not direct agent browser inspection. Owner describes the attached photo as a trash can containing solid/semi-solid waste; the model currently consumes description text only, so this is not image classification evidence. The exact submitted description was not supplied in this confirmation; independent correctness is not established. Correction/defer journeys, unchanged-status browser check and broader model generalization remain separate checks. No production certification claimed.


## 2026-11-20 — Owner Docker demo startup confirmed healthy

Owner-supplied startup output confirms backup `backups/20261120-093046`, successful backend/migration/proxy image builds, healthy PostgreSQL, Mailpit, backend and proxy, completed migration/evidence-init containers and backend readiness HTTP 200. The corrected key-presence build step no longer expands the MapTiler value into the command. This is owner-run startup evidence, not agent-executed Docker inspection or authenticated end-to-end model verification. Next verify generation, correction/defer and persisted history in the Docker municipal browser; Linux model loading/inference is still unconfirmed until an assessment request succeeds. No public beta rollout or formal certification claimed.


## 2026-11-20 — Demo email startup root cause fixed in launcher

Owner logs show email_settings rejecting default capture in production. Local configuration inspection confirmed no production email transport/provider configured (no secrets printed). Launcher omitted the already-established Mailpit override; now includes `compose.production.mailpit.yml`. SMTP stays internal; inbox binds host loopback 8025. Base production settings and fail-closed guard unchanged. This is a launcher correction, not an ML/model/database failure. Owner Docker restart/health verification remains pending due to agent named-pipe access denial. Verified PowerShell parser, merged Compose JSON (values captured without printing secrets), retained migration dependency/read-only model mount, loopback-only inbox, SMTP service construction and continued production capture rejection. No test email sent; no container start performed.

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

## 2026-11-19 — Direct screening of exploratory candidates

Read all 134 candidate descriptions in two complete batches. Recorded per-record hash-bound AI screening decisions in ignored `data/review/exploratory-privacy-pass-v1`, conservatively deferring direct/private identifiers, personal incident context, sensitive allegations and existing spans/holds. Original text and human review forms unchanged. No anonymity, rights approval, independent review or training is claimed. Actual aggregate counts are in its summary; next resolve remaining local-use basis and assess post-deferral class/group support before fitting.

## 2026-11-19 — Deadline exploratory experiment predeclared

Added `research/protocols/exploratory_ai_labels_v1.json`, explicitly separating AI-label agreement from independent accuracy. Reused existing grouped baseline parameters and the 134-record/133-group candidate scope; these are not released training counts. Current source catalogue/API verification via web failed (403/inaccessible); retained metadata declares CC-BY-SA with exact version unresolved. No rights/privacy approval, real training or live inference is claimed. Next directly inspect/redact eligible candidate texts with honest AI-review provenance and resolve documented local-use terms.

## 2026-11-19 — Presentation scope reset

Recorded the owner's November 27 minor-presentation deadline in `MINOR_PRESENTATION_PLAN.md` and current state. This planning-only change prioritizes a real integrated experimental workflow and reserves November 26 for freeze/rehearsal. No model training, deployment, provider call or approval claim occurred. `git diff --check` used; no tests rerun for prose-only changes.

## 2026-11-19 — Reviewed development export contract implemented

Publishing: fetch succeeded after network access was granted and confirmed `main...origin/main` at `0 0` before this commit. Staged diff check passed. Push failed because the Windows Git credential-helper shell could not start (`NtCreateDirectoryObject`, access denied). This checkpoint remains local pending the owner's `git push origin main`. No credential workaround was attempted.

`research/DEVELOPMENT_RELEASE.md` documents the new source-bound review packet and redacted development exporter. Prepared all 271 pilot records at ignored `data/review/development-release-review-v1`, with pending record decisions and false review gates. The actual unreviewed export was refused, exit 1, with no output directory. No real dataset release or model training is claimed.

**277 research tests passed in 26.51s**, including 26 new tests for redaction, Unicode offsets, stale bindings, review gates, coverage, duplicate/group conflicts, minimal exports and failed writes. Original OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Runtime/application dependencies and behavior are unchanged; app tests/builds were not rerun. Real-data baseline execution still refuses every release.

Next complete substantive development review/rights/privacy decisions, preserving AI provenance and unresolved independent review. An assistant-only weak-supervision study needs a separately disclosed protocol, not invented human approvals. The contract is implemented; the review itself is not completed.

Actual commands: `python -m research.civicai_research.release prepare --pilot data/interim/label-pilot-v1 --readiness data/review/baseline-readiness-v2 --context data/review/context-review-validated-v1 --output data/review/development-release-review-v1` succeeded. Corresponding `export` using its pending decisions correctly exited 1. Focused first pass: 25 tests passed in 0.49s; added prepare integration coverage before full `python -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-release-final`: 277 passed. Primary Presidio/scikit-learn sources are linked in the contract document. No private text, decisions or outputs are tracked.


## 2026-11-19 — Synthetic offline baseline implementation

- Added a synthetic-only TF-IDF/logistic-regression runner with grouped validation, a dummy comparator, train-only preprocessing, deterministic selection, provenance hashes, ignored artifacts and incomplete-run markers. Real release inputs fail closed before loading. No real complaint model was trained or deployed.
- Added optional pinned research dependencies and CI installation of `.[test,research]`; production/base dependencies and Docker install commands are unchanged. Consulted primary scikit-learn documentation linked in `research/OFFLINE_BASELINE_RUNNER.md`.
- Editable installation failed twice on this Windows host (temporary-path interpolation, then WinError 3). Installed the five declared research dependencies into the existing virtual environment using the documented binary-wheel fallback. `pip check`: no broken requirements. Early dependency-absent test skips were not treated as successful engine verification.
- Focused engine/gate tests: **23 passed in 23.41s**. Final full command `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-baseline-runner-confirmed`: **251 passed in 28.58s**. A repeat full run was used because the preceding process result was unavailable after context recovery. App suites/builds were not rerun for this offline-only change.
- Actual `python -m research.civicai_research.text_baseline --synthetic --output research/results/synthetic-baseline-2026-11-19-v1` succeeded: 160 records/80 groups/four labels, three folds, six candidates plus dummy, 1,120 predictions, no convergence warnings. This is not research accuracy evidence. The real-release CLI exited 1 and created no output.
- Verified all artifact hashes, current implementation binding, ignored model/prediction files and unchanged base dependencies. Raw OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. No source complaints, keys, private annotations or model binaries are included in this change.
- Updated current state, handoff, decisions and runner documentation. Next: reviewed-release contract/privacy-safe export, retaining the unresolved independent-reference and rights/privacy gates.
- Fetch confirmed the preceding checkpoint was synchronized (`main...origin/main`: `0 0`). Staged diff checks passed. Push of this checkpoint failed because the Windows Git credential-helper shell could not start (`NtCreateDirectoryObject`, access denied). The local main commit awaits the owner's `git push origin main`; no credential workaround or force push was used.

## 2026-11-18 — Baseline candidate assessment and predeclared protocol

- Implemented `baseline_readiness`, joining complete text annotations, pilot group keys, contextual privacy proposals and conservative duplicate containment. All input hashes/identities checked; transitive grouping occurs before filtering, with conflicts/uncertainty deferred. No original groups, records or labels changed.
- Actual run to ignored `data/review/baseline-readiness-v2` exited 0: 157 single-family candidates/156 components; 28 have multiple same-family components. Deferred counts: 33 cross-family, 61 clarification, 16 scope, four unusable. Four proposed development families meet the explicit 20-component engineering floor: 134 records/133 components. All training/reference/privacy eligibility remains unapproved.
- Recorded candidate privacy flags without clearing them (21 span, 16 hold, 55 retention proposal, 65 not context-reviewed), full 12-family support including zero support, and the absent independent holdout. Preserved v1 output and produced v2 after consistency-check/protocol clarification; counts unchanged.
- Predeclared versioned target, model/dummy comparator, feature exclusions, grouped folds, train-only preprocessing, hyperparameters, metrics, fresh reference-test requirement, uncertainty method and provenance. Consulted primary scikit-learn guidance. This adds no estimator dependency and trains nothing.
- Focused tests: **22 passed in 2.03s**. Full `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-baseline-readiness-final`: **228 passed in 21.58s**. No app test/build rerun for isolated research work. Raw OpenCity rehashed unchanged: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- Updated current state, decisions and handoff. Next build/test the offline runner on synthetic fixtures, retaining explicit real-data gates and separate reference/privacy/rights work. No model accuracy, operational release or all-India coverage claimed.
- Confirmed prior synchronization with successful fetch and `main...origin/main` count `0 0`; final artifact/code/policy hashes and staged diff check passed. Only research code/tests/protocol/docs committed. Push failed when the Windows Git credential-helper shell could not start (`NtCreateDirectoryObject`, access denied). This checkpoint remains local pending the owner's `git push origin main`; private inventories are ignored and no credential workaround used.

## 2026-11-18 — Actual text review of all richer pilot annotations

- Read all 271 full descriptions in four bounded batches, covering all 132 unresolved and 139 transferred records. Authored per-record outcomes, component proposals, evidence offsets and uncertainty rationales in ignored local artifacts; this is not a repeat transfer or independent human annotation.
- Final v2 outcomes: 190 described issue, 61 clarification, 16 scope review, four unusable. 366 component proposals; 81 records contain multiple components. Refined six first-pass decisions during consistency review; original v1 is preserved. 102 transferred records have changed tuples, including refinement/additional components rather than an independently measured error count.
- Added `issue_annotations` validation for exact coverage, input/text hashes, evidence spans, allowed fields/family/asset/kind combinations, outcome/context consistency and false approval gates. Preserved source data, prior proposals, privacy review and all application behavior.
- Actual CLI to `data/review/issue-text-validated-v2` exited 0. All output hashes checked. Rehashed raw OpenCity unchanged (`d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`), prior AI responses unchanged and corrected privacy proposals unchanged.
- Focused tests: **33 passed in 3.38s**. Full `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-text-annotations-final`: **206 passed in 20.23s**. App suites/builds not rerun for this isolated research change.
- Consulted primary Label Studio guidance on prediction/review separation. No annotation service or new dependency installed. Updated the report, decisions and handoff; next is baseline readiness and evaluation protocol, not automatic training on AI labels.
- Confirmed the prior owner push with a successful fetch and `main...origin/main` count `0 0`. Final staged diff check passed; only research code/tests and docs were committed, with private annotations/scripts ignored. Publishing this checkpoint failed because the Windows Git credential-helper shell could not start (`NtCreateDirectoryObject`, access denied). The commit remains local pending the owner's normal `git push origin main`; no credentials or force-push workaround used.

## 2026-11-18 — Rich issue-description draft and pilot transfer

Implemented the first versioned family/asset/issue-kind draft in `research/civicai_research/issue_draft.py`; see `research/ISSUE_DESCRIPTION_DRAFT.md`. Applied existing proposals to all 271 pilot records: 139 records yield 153 provisional issue descriptions; 132 remain explicitly unresolved. Unknown setting/time/cause are preserved. This is a deterministic transfer, not fresh text annotation, a fully validated annotation schema or a training release. Original data, active taxonomy, privacy recommendations and application behavior are unchanged. Next directly annotate the unresolved texts and verify transferred descriptions against source evidence.


## 2026-11-18 — Contextual scope/privacy/duplicate recommendation checkpoint

- Confirmed the owner's preceding push: after network access was granted, `git fetch origin` succeeded and `git rev-list --left-right --count main...origin/main` returned `0 0` at `5506b8e`. Initial fetch without that access failed to start name resolution; no credential workaround used.
- Inspected the 41 flagged source-pair titles and all 134 remaining flagged/no-span pilot descriptions. Authored explicit AI recommendations/rationales in ignored `data/review/context-review-authored-v1`; no source prose, private identifiers or per-record labels committed. Scope counts and research-only deferral rationale are in `research/CONTEXT_REVIEW_REPORT.md`.
- Contextual privacy outcomes: 97 retain proposals, 31 restricted-context holds, six new span proposals. Cumulative 43 spans/37 records; no actual redaction or privacy clearance. The other 106 unflagged/no-span pilot records were not assessed in this pass. Inspected the near-text pair and proposed future split containment, retaining both and leaving event identity unverified.
- Implemented offline `review_recommendations` with hash bindings, exact coverage checks, character-offset validation, false approval enforcement, immutable inputs and completion markers. The real CLI run to `data/review/context-review-validated-v1` exited 0. Original raw hash remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- Focused tests: **27 passed in 4.22s**. Full command `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-context-review-final`: **162 passed in 21.26s**. No application tests/build rerun for this isolated research checkpoint.
- Consulted primary Presidio and scikit-learn grouped-validation documentation. No new package/API/model dependency. Updated current state, decisions and handoff; next is a concrete proposal-only record annotation contract, not training or release certification.
- Final staged diff check passed; only research code/tests and documentation were committed. Private authored/validated artifacts and the local authoring script are ignored. `git push origin main` failed because the Windows Git credential-helper shell could not start (`NtCreateDirectoryObject`, access denied). Publication remains pending the owner's normal PowerShell push; no credential workaround or force-push attempted.

## 2026-11-18 — Source-audit checkpoint publication status

- Confirmed the completed QA artifact and clean working tree after implementation commit `c40f5dd`. The preceding regression result remains 135 passing research tests; no implementation changes warrant a rerun.
- Final diff check passed and private QA artifacts/scripts are ignored. Fetch succeeded before the implementation commit, but push failed because Git's Windows credential-helper shell could not start (`NtCreateDirectoryObject`, access denied). The checkpoint is local-only until the owner runs `git push origin main`; no credentials were exposed or alternate credential workaround attempted.
- Remaining work is substantive review, not more training claims: 41 source pairs need scope decisions, three have insufficient source labels, 134 AI-flagged pilot records still lack proposed privacy spans, and the near-text pair needs event adjudication. All current mappings/spans remain proposals; training and independent review are unapproved.

## 2026-11-17 — Source coverage, near-text candidates and privacy spans

- Inspected all 231 source category/subcategory names and created a versioned proposed family crosswalk, committing source-catalogue metadata only under D036. Coverage: 187 family-proposal pairs/14,883 records; 41 scope-review pairs/824 records; three unresolved pairs/364 records. Zero unmatched pairs/unused rules. No record-level reference labels inferred.
- Implemented offline `curation_qa` with indexed input and pilot/proposal binding checks, source membership validation, bounded symmetric token comparison and Unicode offset privacy proposals. No deletion/group merge/redaction/release approval. Existing raw data, forms, taxonomy and application code are unchanged.
- Ran `.\.venv\Scripts\python.exe -m research.civicai_research.curation_qa --proposal data/processed/icmyc-text-proposal-v2 --pilot data/interim/label-pilot-v1 --responses data/review/ai-pilot-complete-v1/responses.json --output data/review/curation-qa-v1`: exit 0. One near-text candidate (23/66, 0.954704, different existing groups); 28 privacy spans/23 records. Not a semantic recall or incident-identity result.
- Assistant inspected all 28 matched spans, trimmed one overbroad address span, retyped one residence reference and added nine missed spans. Separate ignored review artifact contains 37 proposals/31 records; 134 AI-flagged records still lack spans. Text hashes/bounds/nonoverlap asserted. No independent privacy clearance or full-corpus privacy review claimed.
- `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-curation-qa-final`: **135 passed in 14.64s**, including 15 new QA cases. No app-suite/build reruns for isolated research changes. Rehashed raw OpenCity unchanged: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- Consulted primary Python difflib and Presidio documentation; documented direction/autojunk issues and limits of automated privacy detection. No new dependency or external labeling/NLP service configured. Updated current state, decision and handoff references with actual remaining gates.

## 2026-11-17 — Finish all pilot AI proposals and synthesize taxonomy draft

- Read full task descriptions 41–271 in four bounded batches, authored 231 per-task decisions/rationales/privacy concerns and preserved the first 40 responses unchanged. No coordinator key consulted during label authorship. No private source prose or per-record labels enter Git.
- Stored ignored `data/review/ai-pilot-batch-v2` and combined `data/review/ai-pilot-complete-v1`: 271 records, 0 remaining; 125 supported, 14 multiple-issue, 86 gap, 46 unclear. Supported is provisional and may include unresolved public-setting/source assumptions. Proposed privacy concerns: 165; no clearance/redaction performed.
- Extended `ai_labels` with validated disjoint-batch combination, full-coverage enforcement, source provenance, fresh-output requirements and completion markers. Added three tests for complete combination/input preservation, overlap/incomplete/invalid-output rejection and invalid second batch.
- `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-ai-pilot-complete`: **120 passed in 12.47s**. `.\.venv\Scripts\python.exe -m research.civicai_research.ai_labels --pilot data/interim/label-pilot-v1 --responses data/review/ai-pilot-complete-v1/responses.json --require-complete`: exit 0, 271/271, training false. No application changes or app tests/build rerun.
- After proposals were written, checked the coordinator key for tasks 23/66: different proposed groups despite close wording; SequenceMatcher ratio 0.85. Candidate semantic duplicate only, not verified shared incident. No existing group changed.
- Rehashed raw OpenCity: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`; existing human submission count 0. Blank reviewer forms and original data remain intact.
- Created `TAXONOMY_REVISION_PROPOSAL.md` with service-family/asset/issue-kind distinctions, v1 compatibility boundaries and staged adoption requirements. Consulted official scikit-learn target definitions and Label Studio prediction guidance. No new dependency, active taxonomy JSON, final labels, split, model, severity/priority target or deployment change.
- `git diff --check` passed and private outputs are ignored. Fetch succeeded after network permission and main was synchronized before committing. Local commit succeeded; push failed because Git's Windows credential-helper shell could not start (`NtCreateDirectoryObject`, access denied). Owner PowerShell publication is still required; no credentials were printed or bypass attempted.

## 2026-11-17 — Actual AI-assisted annotation batch and boundary findings

- Read the full description of pilot tasks 1–40 and authored 40 explicit AI proposals locally. No coordinator key consulted; prior source/taxonomy context prevents claiming independent blinding. Recorded AI author and unavailable exact model version honestly. Tasks 41–271 remain unread by this pass.
- Stored ignored `data/review/ai-pilot-batch-v1/responses.json` and aggregate summary. Counts: 16 supported, one multiple-issue, 19 taxonomy-gap, four unclear; 22 proposed privacy-review flags. No human forms, raw text, taxonomy, labels/splits, model or app changed. Names/addresses/identifiers were flagged without copying their values into tracked findings.
- Added `ai_labels` structural/provenance validator and 13 cases covering valid partial batches, false approval claims, unknown/duplicate task IDs, text changes, unsupported/inconsistent categories, empty responses, extra fields and missing rationale. Validation does not certify semantic correctness.
- Commands: `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-ai-labels` yielded **117 passed in 11.63s**. `.\.venv\Scripts\python.exe -m research.civicai_research.ai_labels --pilot data/interim/label-pilot-v1 --responses data/review/ai-pilot-batch-v1/responses.json` passed and reported 231 remaining. No app suites/build rerun for isolated research work.
- Consulted official Label Studio prediction documentation; retained prediction/reference distinction without installing services. Recorded taxonomy/service-kind and privacy findings in `research/AI_LABEL_PILOT_FINDINGS.md`. No real incident prose or responses enter Git; raw checksum binding remains unchanged.

## 2026-11-17 — Independent-label pilot preparation

- Added `label_pilot` generation and six regression cases: deterministic/blinded/group-distinct output, changed metadata/selected text, incomplete/overwrite/size boundaries and path escape. Initial two test failures targeted unselected duplicate texts; corrected fixtures to tamper selected inputs rather than claim all unselected files are revalidated.
- Ran `.\.venv\Scripts\python.exe -m research.civicai_research.label_pilot --proposal data/processed/icmyc-text-proposal-v2 --output data/interim/label-pilot-v1`: exit 0, 271 records/groups, COMPLETE; no responses or training approval. The existing proposal index provides provenance; selected text is rehashed, unselected text is not.
- Ran `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-label-pilot-final`: **104 passed in 9.01s**. Application code and data unchanged; no application tests/build repeated.
- Added boundary/adjudication guidance, local privacy precautions and broad-taxonomy gaps in `research/LABEL_PILOT.md`. Consulted official Label Studio annotation guidance; Open311 guide lookup timed out and is not used as evidence. No external annotation service or model installed.
- User confirmed the preceding commit was pushed; initial local main/origin status was synchronized. New generated text/key files remain ignored. No independent review has been synthesized and no final evaluation set assigned.

## 2026-11-17 — Full-corpus text-curation proposal

- Added the offline `research.civicai_research.text_proposal` command, preserving raw records and real-review gates. It verifies input integrity/identities, proposes contact masking, retains complete duplicate-containment membership and reports class support without assigning reference labels or splits.
- Final command: `.\.venv\Scripts\python.exe -m research.civicai_research.text_proposal --snapshot data/raw/icmyc-india-v2 --output data/processed/icmyc-text-proposal-v2`. Exit 0 and COMPLETE observed; derived hashes verified. Earlier development run was stopped and is not final evidence.
- Assessed 16,071 records: 7,289 candidate review, 8,782 targeted review, 264 contact/URL flags, 15,273 containment groups and 14 category-conflict groups. Approved training records remain zero. See `research/TEXT_CURATION_PROPOSAL.md` for class counts and limitations.
- Regression command: `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-text-proposal-final-b`: **98 passed in 12.41s**. Includes 15 new cases for deterministic output, tampering, overwrite/interruption, source preservation, duplicate conflicts and Bengali text. Application tests/builds were not rerun because application code is unchanged.
- Raw OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Raw/derived outputs are ignored; no incident text, credentials, model or fabricated human decisions are included in this commit. Human submissions remain absent.
- `git diff --check` passed. Remote fetch failed with `getaddrinfo() thread failed to start`, including after network permission; remote synchronization cannot be claimed. Publish this checkpoint from the owner's PowerShell if the push encounters the same environment limitation.

## 2026-11-17 — ML decision contract and targeted source audit

- Recorded the owner's agreed direction in `ML_DECISION_SPEC.md`: classification, observable severity and contextual priority separated; provenance/unknown handling, category boundaries, optional assistant scope, offline/shadow rollout, evaluation gates and 17 future acceptance scenarios specified. These are design requirements, not implemented features or passing new tests.
- Completed a bounded 12-query discovery pass and recorded nine additional candidate decisions in `research/DATASET_AUDIT_2026_11_17.md`. Distinguished synthetic data, inaccessible/unverified releases, request-only text/speech research, historical geospatial context and actual incident datasets. No paid access, author messages or model calls were made.
- Retained only public source-card/catalog evidence under ignored `data/external/source-audit-20261117-v1`; no new incident dataset was downloaded. Direct networking initially failed DNS resolution; network permission allowed metadata inspection. India_CIVICS README still returned 401 and the official CPGRAMS guide fetch timed out; both remain unresolved rather than approved.
- Reverified completed acquisition markers, stored hashes for DWSD/Commons/footpath metadata, all 62 pending/unassigned Commons records and the excluded partial footpath snapshot. Original OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- Existing research suite: **83 passed in 9.61s**, command `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-ml-spec-20261117`. No application tests/builds rerun for this documentation-only increment. No dependency, application code, API, taxonomy JSON, raw incident data, annotation, split or model changed.
- Updated source-of-truth links and the handoff's stale immediate-next-step section to reflect the owner-selected research direction while retaining the unverified beta backlog. Next work is OpenCity curation/readiness; training and assistant integration are not started.
- Final documentation verification: 29 local Markdown links resolved, `git diff --check` passed, and all changed files are Markdown. Public metadata snapshots remain ignored. Fetched `origin` successfully; the earlier acquisition commit was still local-only before this increment.
- Local commit succeeded. Publication attempt `git push origin main` failed again because the Windows Git credential-manager shell could not start (`NtCreateDirectoryObject`, access denied). Both this checkpoint and the earlier acquisition commit await an owner PowerShell push; no secret was printed or copied into a workaround.

## 2026-11-16 — Broad Indian civic image acquisition and source audit

- Expanded discovery beyond roads to waste, drains/sewerage, flooding, water supply, streetlights, sanitation, trees/storm damage, debris, pollution, accessibility, public assets, animals and electrical infrastructure. Documented source links, reuse/provenance barriers and category gaps in `research/INDIAN_CIVIC_COVERAGE.md`.
- Acquired West Bengal DWSD v1 (784 images + 784 masks, 252,719,363-byte archive) with matching publisher SHA-256 `fb9229c330ed253f4fb7c18bd46dddebe4df6f8d3f602747f505ff7601a11737`. All archive members pass CRC; images/masks decode at 448×448, matching 784 IDs via the publisher's `img_`/`mask_` convention. No exact RGB duplicates were found; original-scene/augmentation leakage is still unresolved because the paper gives conflicting source-image counts.
- Acquired 62 Commons candidate photos in two ignored snapshots, with 62 distinct source IDs/hashes, per-photo attribution/licenses, null labels, unassigned splits and pending privacy review. Forty-two have West Bengal location terms in their source descriptions/titles. Retrieval topics are not category or severity annotations.
- Downloaded Pune footpath metadata/license and 583 unique publisher severity rows (130 low, 262 medium, 191 high), matching publisher MD5s. Its 4.5 GB image transfer stopped advancing at 55,574,528 bytes and was cancelled; the partial file and `INCOMPLETE` marker remain. A separate metadata-only snapshot completed. No download remains in the background.
- Added `collect_images.py` with source allowlisting, checked redirects, Windows-safe filenames, integrity checks, acquisition limits, no overwrite and explicit incomplete/complete states. No new dependency or application behavior changed.
- Final command: `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-research-expansion-20261116-final` — **83 passed in 5.58s**, comprising the prior 56 research tests and 27 new acquisition cases. An initial new-test collection typo was corrected before this successful run. Backend/frontend tests and production builds were not rerun because their source/configuration/dependencies are unchanged.
- Rechecked the existing OpenCity raw CSV SHA-256: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. No raw record, taxonomy decision, existing review form, split, model or result changed. All new acquisitions remain `training_approved=false`.
- `git diff --check` and staged diff checks passed; only research code/tests/docs were staged and raw/interim data remain ignored. Local commit creation succeeded. `git push origin main` failed because Git's credential-manager shell could not start (`NtCreateDirectoryObject`, access denied), so publishing is still pending a push from normal owner PowerShell. No credential was printed or copied into a workaround.

## 2026-10-17 — Complete engineering handoff audit

Added `docs/AGENT_HANDOFF.md` as the central fresh-agent entry point and reconciled README/current beta documentation with the deployed reality. The audit inventories citizen and municipal capabilities with explicit verification status, documents the actual Render/Supabase/Brevo/Google/MapTiler beta, preserves security and research boundaries, records unresolved beta validation and provides a safe onboarding order. No application behavior, migration, cloud infrastructure, dataset or ML artifact changed.

Verification: 147 backend tests passed with the same three dependency deprecation warnings; 56 research tests passed; all 57 frontend tests passed across four independently invoked test files; TypeScript, Vite production build and `pip check` passed. The sandbox's default temp root remained unwritable, so pytest used workspace-local `--basetemp`. The combined frontend command exceeded the command wrapper limit, so unchanged files were run separately. The OpenCity raw source re-hashed to `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Only placeholder environment examples are tracked; `.env`, `.env.beta` and `.env.production` remain ignored.

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

The first Render attempts exposed two configuration defects before application startup: an incorrect Supabase pooler username followed by a malformed replacement `DATABASE_URL`. Review of the build log also found that Docker's non-empty-key assertion expanded the public MapTiler build key into the build command display. The assertion now checks `process.env` at runtime so no credential value is interpolated into Docker build logs. No application behavior or research state changed.

Verification: 173 research tests passed in 20.07s (`--basetemp tmp/pytest-issue-draft-final2`); 11 new transfer tests. An initial test fixture placed output inside its source directory and correctly triggered the guard; the fixture was corrected and the complete suite rerun. Actual transfer exited 0. Application tests/builds were not rerun because runtime code/dependencies are unchanged. `git diff --check` passed.

## 2026-11-19 — Exploratory fold feasibility and license evidence

Resource-specific publisher metadata identifies CC BY-SA 2.0 and additional credits; datasheet updated. Ran actual StratifiedGroupKFold (3 folds, seed 42) on the 97 AI-screened candidates and validated disjoint groups, complete coverage and every class on each side. Saved counts/hashes privately in `exploratory-privacy-pass-v1/fold-feasibility.json`. No estimator was fitted and no independent accuracy was claimed. Two classes are below the original 20-group planning floor; revise the exploratory protocol explicitly before fitting rather than silently borrowing the original eligibility rule.

## 2026-11-20 — Offline contextual priority foundation

Implemented reported-context-v1 in backend/src/civicai/priority_policy.py; rubric and boundaries in docs/CONTEXTUAL_PRIORITY.md. 69 focused tests passed (all 64 fact combinations plus validation/default cases), two existing dependency warnings. Not wired into API/UI; no database or deployment changes. No full regression rerun needed for this currently unimported pure policy. Next: durable attributed context collection and municipal priority review integration. This is experimental rules-based priority, not image severity or validated municipal triage.


## 2026-11-20 — Contextual priority persistence and municipal panel

Implemented migration 0010, scoped context/review endpoints and municipal panel. Context retains reported source, explicit unknown/conflict, explanation and policy output; separate review history preserves original suggestions. Superseded snapshots reject review; cross-complaint and operator scope are enforced. No complaint status/assignment mutation. Citizen context collection remains pending.

Verification: 540 backend/research tests passed with three known warnings; subsequent focused priority suite 3 passed including newly added operator denial. Existing frontend suite 58 passed; new panel test 1 passed separately after correcting an ambiguous test selector. TypeScript/production build passed. A mistaken Vitest invocation at repository root lacked frontend configuration and failed; corrected frontend invocation passed. Migration 0010 verified in isolated PostgreSQL schemas only. Live Docker rebuild/migration/browser verification remains pending; no deployed completion claim. Next verify this panel through the backed-up local demo launcher, then add direct citizen context collection.


## 2026-11-20 — Priority Docker verification blocked by local access

Attempted the existing backup-first start-ml-demo.ps1 launcher twice, including after granted network permission. Docker Desktop named-pipe permission denied before backup, build, migration or restart. Running stack was not changed. Added exact priority browser checks to ML_DEMO.md. Owner must run the launcher from PowerShell; migration 0010 and priority UI are not yet verified in Docker. Do not repeat completed regression work or claim live completion. Next resume from owner startup output and verify priority history/status preservation.


## 2026-11-20 — Owner priority demo rebuild succeeded

Owner-provided launcher output confirms backup backups/20261120-210821, rebuilt backend/migrate/proxy images, healthy database/Mailpit/backend/proxy, completed migration/evidence-init containers and readiness HTTP 200. Current backend readiness requires schema 0010, so successful readiness supports the migration being applied. This is owner-run output, not direct agent Docker inspection. Authenticated priority generation/review/history browser verification remains pending. No further rebuild is needed before that check.

## 2026-11-21 — Contextual priority browser workflow verified

Used the authenticated local Docker municipal complaint page to exercise the live priority panel. Unknown facts deferred to review; blocked-access context suggested High while displaying unknown service impact; staff acceptance persisted after reload; original context and the review stayed separately visible; complaint status remained Under review. Verification used a clearly labelled demo complaint and demo explanations. No assignment, lifecycle status, citizen evidence, classification review, or external system was changed. Remaining product step: collect the same explicit facts from citizens with truthful attribution and optional/unknown handling.

## 2026-11-21 — Citizen-reported context checkpoint

Added optional all-or-none multipart context, atomic anonymous `citizen_report` priority events, migration 0011, accessible citizen questions and official India 112 safety guidance. Staff suggestions/reviews and complaint lifecycle remain separate. Focused verification: 68 backend tests and 29 frontend tests passed after updating older location tests to target their labelled search field rather than assuming only one combobox. Full verification: 547 backend/research tests with three known warnings, 60 frontend tests and successful production build. No Docker rebuild, development migration or browser submission occurred in this checkpoint.

## 2026-11-21 — Citizen context live journey verified

Owner-run launcher output confirmed backup `backups/20261121-122851`, successful migration 0011, healthy database/Mailpit/backend/proxy and readiness 200. Agent-controlled local Docker browser verification exercised the 112 warning, then submitted demo complaint `64e1b3f3-a550-4a2e-a797-f48cacd64af5` using a generated non-personal PNG, Baranagar search location, danger `no`, access blocked `yes` and service impact `unknown`. Municipal history preserved `citizen report` provenance and all facts, suggested High with the unknown still visible, persisted an explained acceptance after refresh and kept complaint status Submitted. Browser console contained no errors. This verifies one demonstrator path, not policy accuracy, photo analysis, emergency dispatch or production certification.
