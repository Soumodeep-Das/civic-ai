# Bengaluru text-curation proposal

2026-11-17. Status: automated proposal, **not a curated training release**. This completes the computational curation pass authorized after `docs/ML_DECISION_SPEC.md`. It does not manufacture the independent reference labels or human decisions required by Issue #7.

## What the command does

`research.civicai_research.text_proposal` verifies the complete Indian snapshot, raw and publisher-metadata hashes, manifest-referenced text files, record identities and source-label sidecar against the original CSV. CSV parsing preserves embedded newlines and source row identities, including any importer-omitted empty descriptions. Only pending, unassigned, text-only inputs are accepted.

It applies the existing **proposed** source-subcategory mapping without changing the taxonomy or pretending that an `accepted` mapping-rule state is human approval. Each record retains source labels, null `category_label`, pending annotation and unassigned split. It creates separate derived text with proposed contact/URL masking, including spaced Indian phone candidates and overlapping URL/email/phone spans. Original text/files are unchanged. The span log records original offsets and pattern kinds, not matched sensitive values.

Pattern matches include false positives; absence of matches does not prove privacy safety. Names, addresses, identifiers, obfuscated contacts and location descriptions remain unresolved. Derived text is still restricted local data, not safe-to-publish text. Negation, substantive numbers and wording outside proposed spans are retained; no learned normalizer, translation, stop-word removal or text generation is applied.

Grouping links identical normalized original text, identical normalized masked text and digit/URL-normalized templates, then takes transitive components. Numeric/template grouping is conservative containment for review, **not a verified shared incident or a count of independent observations**. It can overmerge different issues and miss semantic duplicates/site bursts. Every member is retained, with no top-20/top-400 truncation. Mixed proposed classes and unresolved mappings in a group trigger review for all its members.

`candidate_review` means an accepted source-rule proposal without detected quality/contact/group concerns; it is not an approved label or privacy decision. `targeted_review` carries explicit reasons. Both routes still need genuine review. Script buckets are not language labels; Latin script does not establish English, and other scripts are retained for language review rather than deleted. No permanent record exclusion, train/test assignment, severity label or priority target is created.

## Reproduce

From the repository root, use a fresh ignored directory:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.text_proposal --snapshot data/raw/icmyc-india-v2 --output data/processed/icmyc-text-proposal-v2
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-text-proposal-local
```

Existing output directories are refused. Choose the next version for a rerun. Only a finished proposal receives `COMPLETE`; write failures retain `INCOMPLETE`. Neither marker grants training approval. No network connection or production database access is used by this command.

Outputs:

| File | Purpose |
|---|---|
| `proposals.jsonl` | Source references/hashes, proposed label, redaction spans, quality/script flags, review route and proposed containment group for every record |
| `texts/` | Restricted derived text copies; never presumed anonymous |
| `groups.json` | Complete component membership, proposed-category conflicts and unresolved-mapping flags |
| `mapping-groups.json` | Every source category/subcategory pair, count and member references for review; no auto-filled reviewer decisions |
| `readiness.json` | Aggregate support before/after screening, group counts, blockers and source/code/mapping/taxonomy hashes; always `training_approved=false` |
| `artifacts.json` | Hashes of all proposal artifacts, including derived text |

The JSONL file is deliberately a proposal schema, not an annotated manifest accepted by the training-preparation tool. Stage A forms/submissions are neither edited nor synthesized. Final reviewed derivatives and source/group adjudication remain separate work.

## Observed full-corpus support (2026-11-17)

Final local output: `data/processed/icmyc-text-proposal-v2`. Algorithm version is `icmyc-text-proposal-v1`; directory v2 identifies the final run rather than a taxonomy change. The earlier development run was stopped and is not release evidence.

All 16,071 records were assessed across 231 source category/subcategory pairs. Existing rule states remain 7,843 accepted proposals, 2,255 ambiguous, 5,955 needing review and 18 rejected proposals. No records were permanently removed. Screening routes 7,289 to candidate review and 8,782 to targeted review; **zero records are approved for training**.

| Proposed category | Accepted source-rule candidates | Candidates without detected screening concerns | Proposed groups among those candidates |
|---|---:|---:|---:|
| garbage_waste | 3,350 | 3,133 | 2,998 |
| road_damage | 2,252 | 2,136 | 2,063 |
| streetlight | 1,294 | 1,180 | 1,130 |
| drainage_sewerage | 360 | 321 | 318 |
| broken_footpath | 305 | 250 | 246 |
| waterlogging | 226 | 216 | 212 |
| water_leakage | 56 | 53 | 53 |
| other | 0 | 0 | 0 |

These are workload/support counts, not accuracy, ground truth or independently verified incidents. The zero `other` count means no accepted rule for that category, not absence of other civic issues. Waste/road dominance and sparse water leakage require an explicit support plan; do not invent balance with synthetic evaluation data or equate the proposed taxonomy with all civic issues.

The pass proposes 15,273 containment groups, including 342 multi-record groups, largest size 49. Fourteen groups have conflicting proposed categories (60 records). Contact/URL patterns flag 264 records; 616 have extremely short text. Counts overlap. Script screening finds 16,034 Latin-script records and 37 unknown/other-script records; no Bengali-script support is established. Names/addresses and semantic/event duplicates still need review.

OpenCity raw SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Source/code/mapping/taxonomy and output hashes are recorded locally. The existing human-submissions directory was empty at this checkpoint. Tests: **98 research tests passed**, including 15 new proposal cases; synthetic test fixtures are never incident observations.

## Methodology and limits

The [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html) requires learned preprocessing to fit only training data. [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html) keeps supplied groups separate; it does not discover or verify incidents. This pass only proposes dataset-wide duplicate containment and deterministic masking before any split; no vocabulary, imputer, classifier or scaler is fitted.

Before a real experiment: resolve taxonomy and source mappings, review privacy, establish independent category references, adjudicate template/semantic/event groups, confirm derivative terms, report class/language/city support and freeze a justified split protocol. A class with no screened candidates cannot be silently synthesized from unrelated records. Bengaluru-only support is not West Bengal generalization. Neither source labels nor simulated priority values are gold civic severity judgments.
