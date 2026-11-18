# Contextual scope, privacy and duplicate recommendations

2026-11-18. This completes the **AI recommendation pass** over the 41 flagged source pairs, 134 pilot records with privacy concerns but no spans, and one near-text duplicate candidate. It does not adopt a taxonomy, redact source text, determine legal jurisdiction or approve training. Original data, reviewer forms, existing groups and the application are unchanged.

## Scope recommendations

The assistant inspected all 41 source category/subcategory names. These are catalogue-level recommendations for the initial physical civic-condition research target, not decisions about every associated complaint. Broad CivicAI reporting remains broader than this first experimental target; no record is deleted or declared an invalid grievance.

| Recommendation | Source pairs | Associated records |
|---|---:|---:|
| Defer administrative, conduct and enforcement requests from the initial physical-condition target | 30 | 512 |
| Include only if record text establishes a relevant public asset | 4 | 33 |
| Decide from the actual reported condition, not the source title | 4 | 269 |
| Specialist fire-safety scope/evidence review | 3 | 10 |
| Total | 41 | 824 |

- Deferred source titles concern certificates/tax, pension/ration/personnel administration, historical COVID-rule enforcement, policing/personal conduct and individual transport offences or meter disputes. Retain for broader service-grievance work. Actual text may justify a different disposition; source titles cannot supply reference labels.
- Conditional public assets: housing quarters, shopping/commercial complexes and surveillance-camera installation/maintenance. Establish public service relevance rather than assume every private building or camera belongs in an infrastructure class.
- Record-context decisions: unauthorized construction, hawkers/vendors, no parking and one way/no entry. Separate actual obstruction, waste or a missing sign from licensing, livelihood or individual conduct disputes. An allegation does not establish illegality.
- Fire exits, pumps and other fire-safety reports stay under specialist review. Do not infer safe handling, emergency status or severity from their source names alone.

The three previously unresolved source pairs (364 records) remain unresolved. The 187 prior family-proposal pairs remain unchanged. None of these counts are validated class support, individual annotations or all-India coverage.

## Contextual privacy inspection

The assistant read all 134 pending pilot descriptions and authored individual rationales. These records were selected because the earlier AI pass flagged concerns and the corrected span proposal supplied no span. This pass is deliberately narrower than a full privacy audit of all 271 pilot texts, let alone the 16,071-record corpus.

| Recommendation | Records | Meaning |
|---|---:|---|
| Retain context proposal | 97 | Public roads/landmarks, generic residences or already masked contacts; no additional direct identifier selected in this pass |
| Hold sensitive context | 31 | Residence linkage, health/injury, private disputes or allegations need further judgment; not necessarily a confirmed privacy violation |
| Propose an additional span | 6 | Specific residence/property references and one possible personal-name token |

The six new proposals bring the combined artifact to **43 spans in 37 records**, including the prior 37 spans in 31 records. Offsets refer to Unicode characters in the already pattern-masked pilot text. No source bytes or pilot text were changed. One possible trailing name is uncertain; it remains a proposal. At least one newly spanned record also contains an allegation requiring contextual judgment: redacting a name is not clearance of the rest of the text.

The remaining **106 records without an earlier concern or span were not assessed in this contextual pass**. Absence of a flag is not proof of safety. The 97 retain recommendations are not privacy approval; public locations can still be identifying when linked with other data. Per-record rationales and offsets remain in ignored local artifacts, not Git. No raw complaint prose or matched private strings are included in this report.

[Presidio's primary documentation](https://presidio.dataprivacystack.org/) warns that automated detection cannot guarantee finding all sensitive information. We preserve that limitation and use contextual judgments instead of converting every location into a redaction. No external labeling service, new NLP dependency or privacy certification is introduced.

## Duplicate recommendation

The assistant compared both texts of the sole lexical candidate (pilot tasks 23/66). Near-identical narrative and compatible contextual cues justify **proposing joint containment in a future split**, retaining both originals. They do not prove the same incident. Event identity stays unverified; no group merge, row deletion or split assignment occurred. The local rationale records the basis without publishing identifying values.

[scikit-learn's grouped cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data) explains why dependent observations need group-aware separation. Our recommendation is conservative leakage containment, not evidence that a particular incident occurred twice or an implemented split. Corpus-wide duplicate/event review remains outstanding.

## Artifacts and validation

- Authored ledger: ignored `data/review/context-review-authored-v1/recommendations.json`; SHA-256 `2789922b3dae0e590334f82f7c56c5a2d4113f7219a98264c9f746c96c4b183d`.
- Validated output: ignored `data/review/context-review-validated-v1`, containing a copy of recommendations, cumulative privacy-span proposals, aggregate summary, artifact hashes and COMPLETE marker.
- Original corrected-span input remains unchanged at SHA-256 `014aec50ef9251a25c7cb85990980af5fa1a09c3939c7a6710a7a339f794c952`.

`review_recommendations` verifies indexed QA/pilot inputs, QA-to-pilot binding, task text hashes, complete exact review coverage, unique identities, bounded nonoverlapping character spans and allowed dispositions. It refuses human-author claims, approval flags, merges, event-identity approval, unexpected fields and output overwrite. It does not validate the semantic truth of an AI judgment, authenticate deliberately rewritten hash indexes, or create a release. All three flags remain false: training approval, privacy approval and independent review completion.

Run from the repository root, using a **fresh output directory** for a rerun:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.review_recommendations --qa data/review/curation-qa-v1 --pilot data/interim/label-pilot-v1 --prior-privacy data/review/curation-qa-span-review-v1/privacy-spans.json --recommendations data/review/context-review-authored-v1/recommendations.json --output data/review/context-review-validated-v2
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-context-review-rerun
```

The actual validation command used output `context-review-validated-v1` and exited 0. The authoring judgments are stored locally; rerunning validation checks those judgments rather than independently reproducing them. A fresh clone does not contain private review data.

Verification: **27 new contract tests passed**, then **162 research tests passed in 21.26s** using `--basetemp tmp/pytest-context-review-final`. Synthetic cases cover Unicode offsets, stale hashes, missing/extra/duplicate decisions, input mismatch, false approvals, invalid spans, event-identity/merge refusal, deterministic output, input preservation and interrupted writes. Application tests/builds were not rerun because application code and dependencies are unchanged.

The actual raw OpenCity file was rehashed and remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Original source labels, null/pending CivicAI labels and unassigned splits remain unchanged. No classifier, image severity model, priority model or chatbot was trained or deployed.

## Next intended step

Encode the draft service-family/asset/issue-kind distinctions and these scope outcomes in a versioned **proposal-only annotation contract**, then apply it to the existing pilot with explicit ambiguous and multiple-issue outcomes. Preserve taxonomy v1 and the original proposals. This is concrete record-level research work, not another source search or blank review form.

Independent reference adjudication, rights/derivative review, remaining contextual privacy decisions, full-corpus leakage checks and class/language support still precede a validated training release. Human submissions remain absent; do not convert AI proposals into independent evaluation truth.
