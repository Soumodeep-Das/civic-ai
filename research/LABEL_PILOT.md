# Independent-label guideline pilot

2026-11-17. Generated, not annotated or training-approved. This is the next small step after the full-corpus proposal: establish whether complaint text supports the proposed category definitions before expanding annotation. No model or production behavior changes.

## Local artifacts and reproduction

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.label_pilot --proposal data/processed/icmyc-text-proposal-v2 --output data/interim/label-pilot-v1
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-label-pilot-final
```

Use a fresh output version for reruns. The command verifies the completed proposal's indexed readiness/record files and every selected text against recorded checksums. It does not rehash unselected texts or independently authenticate a maliciously replaced hash index. Output records the input index, taxonomy and generator hashes. No raw snapshot or existing review form is edited. Interrupted outputs remain INCOMPLETE; COMPLETE means generation only.

Actual local output: **271 records from 271 proposed containment groups**, with at most 20 per proposed-category/review-route stratum. Seven candidate strata contribute 140 records; targeted strata contribute 131 (including 20 unmapped cases). Small strata contribute two water-leakage and nine waterlogging cases after group deduplication. This is a purposive guideline pilot, not a representative prevalence sample, final test set or estimate of independent incidents. Source-category sampling can miss wrongly mapped examples; later coverage work must examine all 231 source pairs.

- `reviewer/tasks.json`: complaint text, opaque task ID and blank response fields only. Source category, sampling route and proposal are hidden. Text is JSON, never executable HTML or spreadsheet formulas.
- `reviewer/taxonomy.json`: unchanged proposed v1 definitions.
- `coordinator/key.json`: restricted task-to-source/group key and proposals; do not show this to independent reviewers before they submit.
- `coordinator/summary.json`: sampling counts, hashes and explicit non-approval state.
- `artifacts.json`: output integrity index. All artifacts remain ignored local files.

Folder separation is an operational convention, not access control. Restrict the coordinator files through filesystem permissions if sharing the reviewer folder. Do not upload either folder to a public issue or external AI service: masked text can still contain names/addresses. The pilot has no production/debug web endpoint and no automatic submission importer. Completed responses are not automatically compatible with Issue #7 decision forms or sufficient for release approval.

## Reviewer instructions

Use the description alone; do not infer a defect from the hidden source label, urgency from capital letters, or severity from repetition. Reviewers must record their actual identity code and timezone-aware review time. Leave uncertainty explicit. Never copy the proposed label as independent truth.

Choose `decision`: `single_issue`, `multiple_issues`, `unclear`, `outside_scope`, or `needs_language_review`. Fill `category` only for a supported single issue; use `additional_categories` for multiple supported issues. Give a short rationale without repeating personal information. Record the observed language without assuming Latin script means English. Set `privacy_action` to `needs_redaction`, `exclude`, or `reviewed_no_action`; the last requires actual inspection, not absence of regex flags.

| Boundary | Apply |
|---|---|
| Pothole versus request for a new road | Existing carriageway damage supports road_damage; new paving/service requests need scope review. |
| Broken footpath versus blocked footpath | Structural pedestrian-surface damage supports broken_footpath; parked vehicles/debris do not establish damage. |
| Garbage versus missed collection | Visible accumulated waste supports garbage_waste; a collection-service request alone must not be silently redefined as dumped waste. |
| Streetlight fault versus installation | Fault in existing public lighting supports streetlight; new installation is a distinct service request. |
| Standing rainwater versus sewer overflow | waterlogging when accumulation is described; drainage_sewerage when drain/sewer defect or overflow is explicit. Multiple explicit issues can remain multi-issue. |
| Supply leak versus shortage | water_leakage requires unintended escape from public supply infrastructure; low pressure/no supply is not a leak. |
| Other versus unclear | other requires a clear eligible civic issue outside the named classes; vague text is unclear, never a convenient other label. |
| Alleged danger/emergency | Record the described issue without assigning urgency/severity; the current non-emergency taxonomy may be unsuitable. No operational emergency advice is inferred by this offline tool. |

Negation matters: “no pothole, only rubbish” does not support road_damage. Historical/resolved statements and requests for inspection may not establish a current defect. If masking removes decisive context, mark unclear/privacy review. These are synthetic instructions, not dataset observations.

## Broader civic coverage cannot be forced into eight labels

The source inventory has substantial unresolved support beyond v1: Animal Husbandry 859 records, Pollution 437, Traffic and Road Safety 967, Water Supply and Services 277, and Trees and Saplings 104 (counts of non-accepted source-rule proposals, not verified class labels). Parks, sanitation/public toilets, electricity and new-infrastructure requests also exist. Do not discard them or label them all other. A future versioned taxonomy should distinguish service family from issue subtype and review municipal scope; public reporting stays broader than the currently supported classifier.

Before full annotation, independently review this pilot, compare disagreements, revise definitions with versioning, and re-review affected cases. A second AI pass is not an independent human reference. If human review remains unavailable, AI-assisted exploratory labeling must be explicitly scoped and cannot silently pass the existing training/evaluation gates. No agreement statistic can be reported before real submissions exist.

Method reference: [Label Studio labeling guidance](https://labelstud.io/guide/labeling.html) supports explicit annotation instructions, skipping uncertain tasks and multiple annotations. We use a local JSON pilot without installing a labeling service; source-label blinding is our design decision, not a claim of formal study validation.
