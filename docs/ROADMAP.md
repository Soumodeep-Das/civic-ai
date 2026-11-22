# Scope, limitations and major-project roadmap
Updated November 22, 2026. Future items are proposals with acceptance criteria, not scheduled or implemented features.

## Minor deliverable and original synopsis

The original synopsis proposed a controlled text-only, image-only and multimodal classification comparison plus a priority prototype. The delivered minor scope consists of a working complaint-management application, a small exploratory text experiment and an integrated human-reviewed contextual-priority policy. The image and multimodal comparisons remain unfinished; this is an explicit scope gap, not a claim that the original research objective has been met.

| Area | Delivered minor scope | Remaining limitation |
|---|---|---|
| Reporting | Description, photo, confirmed location, reported impact | No offline submission or status notifications |
| Identity | Guest tracking, optional citizen accounts, Google OIDC, municipal roles | No claim of independent security certification |
| Operations | Department ownership, queues, lifecycle/history, review explanations | No municipal integration, guaranteed response time or automatic routing |
| Text ML | 97 Bengaluru texts; four families; TF-IDF/logistic regression | AI labels, small sample, selected development-fold metrics |
| Priority | Rules over reported danger/access/service facts | No independently validated urgency targets or learned ranking |
| Images | Protected upload/storage/display | No image classifier, severity model or automatic captioning |
| Deployment | Local HTTPS demo; portable Compose and closed-beta configuration | Single-host operation; current beta ML activation is unverified |

## Research limitations to state explicitly

The 16,071-record source size is not the training-set size. Only 97 screened descriptions were used in the exploratory fit. Three development folds informed model selection; there is no untouched independent test result. The reported macro-F1 measures AI-label agreement. It cannot establish operational quality, calibration or all-India accuracy.

The model's four families do not cover all civic issues. Unsupported complaints remain valid and require staff review. The heuristic guard has no comprehensive language, negation or out-of-distribution guarantee. Bengali/Hindi, West Bengal transfer, mixed issues and rare wording require dedicated evaluation.

Available image candidates do not form an approved, representative paired dataset. West Bengal source acquisition is documented in the [coverage inventory](../research/INDIAN_CIVIC_COVERAGE.md); it does not establish a trained West Bengal model. Source licenses, personal information, duplicates and independent labels need source-specific decisions.

## Major-project work in dependency order

| Workstream | Intended improvement | Evidence needed to call it complete |
|---|---|---|
| 1. Independent Indian reference set | Broader civic services, Kolkata/West Bengal and language coverage | Rights/provenance review, documented annotation guide, independent adjudication, per-class/city/language support |
| 2. Stronger text evaluation | Measure transfer and abstention beyond AI-label development folds | Frozen grouped test set, baseline comparison, per-class errors, coverage and calibration analysis where probabilities are exposed |
| 3. Image task and genuine pairs | Evaluate visible defects and image/text classification | Compatible labels, independent scenes, event/source split controls, aligned incident pairs and equal held-out comparisons |
| 4. Severity and contextual ranking | Incorporate evidenced condition, duration and exposure | Category-specific observable rubric, municipal/domain review, unknown/conflict handling and under/over-triage evaluation |
| 5. Citizen communication | Status notifications and clearer follow-up | Delivery/retry tests, privacy controls and usable citizen history |
| 6. Product usability | Better map refinement, accessibility and multilingual guidance | Physical-device and keyboard/screen-reader checks; comprehension and language testing |
| 7. Operational readiness | Dependency locking, monitoring, abuse controls and recovery | Repeatable environment, capacity measurements, off-host restore exercise, shared rate limits where required |
| 8. Optional AI assistance | Bounded description/observation help | Selected provider/local model, disclosed data handling, measured costs/resources, failure limits and human confirmation |

A general chatbot is not needed to demonstrate the core project. Optional assistance must not be presented as CivicAI-trained research or as independent evaluation truth. See [photo-assistance decision](PHOTO_ASSISTANCE_DECISION.md).

## Engineering debt visible in the implementation

- Python uses dependency ranges with pinned research packages, but no complete resolved lockfile.
- Inference is synchronous and reloads the artifact on generation; production latency/resource budgets are unmeasured.
- Repeating assessment or priority writes can add events; no global retry-idempotency mechanism exists.
- Priority reviews reject superseded context, but database-trigger immutability is not uniform across all experimental event tables.
- Base images/public clones omit the private model; CI skips the real-model test when that file is absent.
- Login throttling is process-local. There is no high availability, distributed abuse-control service or formal recovery-time guarantee.
- Map, geocoding, OIDC and email availability depend on configuration and external providers.
- The citizen success message still says evidence is visible only to municipal staff, although the API also permits the authenticated owner. This UI-copy mismatch is recorded for a later code change; the access boundary is documented accurately here.
- A successful backup command does not establish successful restoration.
- No repository software license has been selected. Dataset licenses do not license the application code.

## Before the presentation

Use the [demo runbook](MINOR_DEMO_RUNBOOK.md), rehearse the exact machine/profile and keep an honestly labelled fallback recording. Feature freeze allows documentation improvements and fixes for demonstrated blockers. Acceptance of the minor demo does not close the major research gaps above.
