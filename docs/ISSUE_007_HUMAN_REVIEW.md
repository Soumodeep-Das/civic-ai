# Issue #7 — Human-reviewed Indian text curation and taxonomy approval

Status: **Stage A infrastructure complete; awaiting real human review. Stage B has not started.**

Evidence labels: **VERIFIED FACT** is reproduced from retained artifacts; **PROJECT DECISION** is enforced by code; **PROPOSED DECISION** needs human approval; **HUMAN REVIEW DECISION** must come from a validated reviewer submission; **UNRESOLVED** is not treated as accepted.

## Scope and exclusions

Stage A creates an offline review package, schemas, validators, conflict/adjudication handling, deterministic redaction primitives and a fail-closed curation-readiness gate. It does not train a model, assign labels, approve the taxonomy, resolve license terms, create a final split, or build a curated dataset without human input.

The immutable source remains `data/raw/icmyc-india-v2`. The generated review package is `data/interim/issue7-review-v5`; both are ignored by Git. Package hashes bind it to dataset `icmyc-d951dbb48453`, raw SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`, Issue #6 audit v5, the proposed taxonomy/mapping, schema and generator code.

## Generated human queues

| Form | Items | Human task |
|---|---:|---|
| `taxonomy_review.csv` | 8 | Assess definitions, exclusions, confusions, evidence and support; pay special attention to `other`. |
| `mapping_review.csv` | 231 | Review every distinct original category/subcategory pair with support and three reproducibly sampled, locally redacted previews. |
| `privacy_review.csv` | 201 | Decide no action, deterministic redaction, exclusion or additional review for distinct phone/email-flagged records. Regex matches are not assumed to be PII. |
| `record_review.csv` | 1,406 | Review the union of Issue #6 suspicious records and mapping examples for label/exclusion/adjudication/language evidence. This is an initial priority queue, not a claim that every ambiguous subgroup has been annotated. |
| `duplicate_review.csv` | 400 | Decide whether the largest detected duplicate/template groups represent linked incidents, separate incidents, exclusions or unresolved cases. |
| `license_review.csv` | 1 | Resolve local use/redistribution status and attribution implications as far as evidence allows. |
| `dataset_approval_review.csv` | 1 | Leave blank until every prior gate is complete and conflicts are adjudicated. |

No human decision is prefilled. Previews replace detected phone/email patterns, are limited to 240 characters and stay in the ignored local package. Source text is never written to committed documentation.

## Reviewer workflow

1. Each reviewer copies only the assigned form from `forms` into `submissions` and adds their pseudonymous code to its filename.
2. Fill only `reviewer_id`, `reviewed_at`, `decision`, `reviewer_rationale` and the outcome columns to their right. Preserve all context columns.
3. Use an ISO-8601 timestamp with timezone. Review independently; do not inspect another reviewer's file first.
4. Validate each file:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.review validate `
  --package data/interim/issue7-review-v5 `
  --submission data/interim/issue7-review-v5/submissions/mapping_review_reviewer01.csv
```

5. Merge one or more validated submissions into a new ignored output:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.review merge `
  --package data/interim/issue7-review-v5 `
  --submission data/interim/issue7-review-v5/submissions/mapping_review_reviewer01.csv `
  --submission data/interim/issue7-review-v5/submissions/mapping_review_reviewer02.csv `
  --output data/processed/issue7-decisions-v1
```

6. If conflicts exist, independent adjudication uses the generated `adjudication_review.csv`. Validate it before Stage B:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.review validate-adjudication `
  --decisions data/processed/issue7-decisions-v1/decisions.json `
  --adjudication data/processed/issue7-decisions-v1/adjudication_review.csv
```

Apply only validated adjudications into a new decision file:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.review apply-adjudication `
  --decisions data/processed/issue7-decisions-v1/decisions.json `
  --adjudication data/processed/issue7-decisions-v1/adjudication_review.csv `
  --output data/processed/issue7-decisions-v1/decisions-adjudicated.json
```

Partial submissions are supported and may be resumed. Duplicate submissions by the same reviewer for the same item are rejected. Different decisions are never silently collapsed.

## Validation and curation gates

The schema permits only documented states. Mapping approval must retain its proposed category; a different category is a proposed revision, not silent reinterpretation. Record exclusions require reasons. Complex name/address/identifier redactions require explicit character spans. Duplicate `keep_together` decisions require an approved stable group ID.

The Stage A curation skeleton can produce a readiness report only after decisions exist:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.curate `
  --package data/interim/issue7-review-v5/package.json `
  --decisions data/processed/issue7-decisions-v1/decisions.json `
  --output data/processed/issue7-readiness-v1
```

It fails closed: missing items, conflicts, taxonomy revisions/discussion, ambiguous or record-level mapping states, pending privacy/record/duplicate review, unresolved/rejected license review, or absent explicit dataset approval keep `training_approved` false. A readiness report is not a curated dataset.

## Safety and methodology decisions

- **PROJECT DECISION:** raw data remains immutable; all forms and submissions are ignored local artifacts.
- **PROJECT DECISION:** automated proposals/previews never become human decisions.
- **PROJECT DECISION:** identical wording alone does not prove one incident; human duplicate decisions are preserved.
- **PROJECT DECISION:** script buckets are not language labels; reviewers may record only observed English, transliterated Indian, mixed, unclear or unusable evidence.
- **PROJECT DECISION:** spreadsheet-facing fields are quoted and formula-leading values are escaped; reviewers still use Protected View because [OWASP notes that CSV formula mitigations are not universal](https://community.owasp.org/attacks/CSV_Injection).
- **UNRESOLVED:** whether taxonomy v1, especially `other`, is supportable.
- **UNRESOLVED:** which mapping groups can safely label whole subgroups and which need expanded record-level review.
- **UNRESOLVED:** exact OpenCity derivative redistribution rights.
- **UNRESOLVED:** final duplicate/event groups, class support and split method.

## Stage B entry condition

Stage B begins only after the user supplies validated human submissions. If mapping decisions request record-level review beyond the initial 1,406-item queue, Stage B must generate that additional queue and pause again rather than guessing labels. No model training begins until the final derivative and training-approval gate explicitly pass.
