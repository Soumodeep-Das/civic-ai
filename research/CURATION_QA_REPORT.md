# Source coverage and pilot privacy/duplicate QA

2026-11-17. Completed the source-pair coverage pass and bounded pilot QA proposal pass. **Not a curated release, independent adjudication or training approval.** Active taxonomy v1, original records, existing duplicate groups and application behavior remain unchanged.

## All source pairs accounted for

The assistant inspected all 231 source category/subcategory names and authored an explicit proposed crosswalk in `mappings/icmyc_family_draft_v1.json`. It binds to the existing source-pair artifact hash. The crosswalk contains source catalogue names, draft families/scope flags and rationale only—no complaint text, record IDs, personal data or per-record labels. `curation_qa` verifies source membership counts/overlap and input hashes, then produces the complete local coverage table.

| Disposition | Source pairs | Associated records |
|---|---:|---:|
| Draft family proposal | 187 | 14,883 |
| Explicit scope review | 41 | 824 |
| Insufficient source-label information | 3 | 364 |
| Total | 231 | 16,071 |

All input pairs have an exact rule; no rule is unused. The three unresolved pairs are the NULL/NULL and two Others variants. Administrative certificates/tax/benefit requests, policing, fire safety, historical COVID-rule reports and other regulatory/private scope questions are retained for review, not silently excluded. Their legal or municipal jurisdiction has not been determined by this audit.

Candidate family support (nonexclusive; includes some scope-review records and ambiguous multiple-family rules):

| Draft family | Source-associated records |
|---|---:|
| roads_and_pedestrian_access | 5,061 |
| solid_waste | 4,210 |
| public_lighting | 1,517 |
| mobility_and_traffic_infrastructure | 1,043 |
| animals | 831 |
| drainage_and_sewerage | 687 |
| sanitation_and_public_health | 534 |
| pollution_and_nuisance | 482 |
| water_services | 355 |
| parks_trees_and_waterbodies | 277 |
| public_assets_and_space | 268 |
| electricity_services | 256 |

These are **source-catalogue associations, not validated class support or model accuracy**. Issue kind is deliberately left `requires_record_review`; a label such as maintenance/installation can encompass distinct actions. Multiple-family candidates include bridge/culvert and ambiguous cable labels. Every record still needs textual/reference review before training eligibility. Broad source-family coverage does not establish all-India, Bengali or image coverage.

## Duplicate proposal findings

Compared all 271 pilot texts using normalized word tokens, preserving numbers and negation. The conservative score is the minimum of both directional SequenceMatcher ratios with `autojunk=False`. Threshold 0.82 is an engineering review trigger, not an evaluated classifier or tuned research result. A length bound and token-overlap upper bound avoid unnecessary comparisons; near-matching texts shorter than five tokens are skipped unless exactly equal. Short identical phrases are marked generic. Inputs over 1,000 records or 20,000 characters per text fail rather than silently truncate.

One pair was proposed: tasks 23/66, score **0.954704**, crossing existing proposed groups. It is the wording-similar pair noted in the preceding report. The previous 0.85 figure used raw characters and default SequenceMatcher; the scores are from different methods and not competing performance metrics. Shared wording does not prove the same incident. No automatic merge, deletion or split assignment occurred. No other candidate above this trigger does **not** establish absence of paraphrases or duplicates elsewhere in the 16,071-row corpus.

The [Python difflib documentation](https://docs.python.org/3/library/difflib.html) describes automatic-junk and direction-sensitive behavior. We disable automatic junk and compare both directions. This is lexical candidate generation, not a semantic embedding model or an exhaustive incident-linking solution.

## Privacy proposals and actual inspection

The automatic pass proposes offset spans for contact patterns, signature/name cues, address cues and complaint identifiers. Offsets are Unicode character positions in the **pilot's already pattern-masked text**, not bytes or raw-CSV offsets. Spans merge overlaps and store kinds/offsets rather than matched sensitive strings. No masking is applied by this pass.

- Automatic pass: 28 spans in 23 records; 142 AI-flagged records had no matched span.
- The assistant inspected every automatic match. One address span also captured an unrelated complaint clause; its proposed end was shortened. One signature-like span was identified as a residential-location reference rather than a personal name.
- Added nine specific missed name/address/identifier spans after inspecting their source text. The revised proposal has **37 spans in 31 records**, with **134 AI-flagged records still lacking a span**.

The additional inspection is AI-assisted, not independent human privacy adjudication. The 134 records include public landmarks, allegations, residence details and other contextual concerns; absence of a span does not mean each has a confirmed disclosure, nor does it clear them. Unflagged records can also contain sensitive information. Multi-line/embedded addresses, spelling variation and non-Latin names remain weak spots. Removing a public issue location may harm meaning, so public landmarks and personal residential addresses require different judgments.

The original pattern output is immutable. Corrected proposals live separately in ignored `data/review/curation-qa-span-review-v1`; output SHA-256 `014aec50ef9251a25c7cb85990980af5fa1a09c3939c7a6710a7a339f794c952`. The local script asserted text hashes, bounds and nonoverlap. It does not constitute an approved redaction engine or a publication-safe dataset. No source text, matched private values or per-record corrections are committed.

[Presidio's documentation](https://presidio.dataprivacystack.org/) explicitly warns that automated detection cannot guarantee finding all sensitive information. We retain this limitation; Presidio, external NLP services and new model dependencies were not installed.

## Reproduce and inspect locally

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.curation_qa --proposal data/processed/icmyc-text-proposal-v2 --pilot data/interim/label-pilot-v1 --responses data/review/ai-pilot-complete-v1/responses.json --output data/review/curation-qa-v1
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-curation-qa-final
```

Use a fresh output directory for reruns. Generated files: `source-coverage.json`, `near-duplicates.json`, `privacy-spans.json`, `summary.json`, `artifacts.json`, and COMPLETE. Only proposal generation completed; training/privacy/event identity remain unapproved. Read-only AI span inspection is retained separately with input/output hashes; rerunning the algorithm alone does not reproduce those judgment-based corrections.

Verification: **135 research tests passed in 14.64s** (15 new cases); actual command exited 0. Tests cover UTF-8/offset boundaries, overlapping spans, symmetric candidates, numeric/negation differences, short generic text, comparison limits, duplicate/invalid source rules, source-count overlap, input tampering, partial pilot rejection, deterministic outputs, input preservation and interrupted writes. Application suites/builds were not rerun because the application is untouched.

Raw OpenCity SHA-256 was rechecked: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Indexed proposal metadata and selected pilot artifacts are checked; this command does not rehash all 16,071 source text files or authenticate a maliciously rewritten hash index.

## Next gate

Use the coverage table to scope a versioned record-level annotation contract, resolve the 41 scope-review pairs, review near-duplicate membership and finish contextual privacy decisions. Maintain a separate AI-proposal trail if the team remains unavailable. Independent reference adjudication, rights/derivative review, actual per-class/language support and leakage-controlled split approval still precede a validated training release. Do not manufacture reviewer approval or call these candidate counts model results.
