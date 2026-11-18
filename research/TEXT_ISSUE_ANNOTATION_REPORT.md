# Text-grounded issue annotation of the complete pilot

2026-11-18. The assistant read all 271 pilot descriptions in four bounded batches during this checkpoint: 1–70, 71–140, 141–210 and 211–271. It authored new service-family/asset/issue-kind proposals using exact text spans, covering both the 132 previously unresolved records and the 139 transferred records. This is an actual AI text-review pass, not another automatic transfer. The assistant has prior source context and is not an independent or blinded reference annotator.

## Results of this pass

| Record outcome | Previously unresolved | Previously transferred | Total |
|---|---:|---:|---:|
| Described civic issue | 69 | 121 | 190 |
| Clarification needed | 43 | 18 | 61 |
| Scope review | 16 | 0 | 16 |
| Unusable text | 4 | 0 | 4 |
| Total read | 132 | 139 | 271 |

There are **366 issue-component proposals**, with multiple components in **81 records**. Components can describe different conditions on the same asset, requests versus defects, or alternatives requiring clarification. They are not independent incidents. Of the 190 described-issue records, 129 have a single component; this is not an approved training subset or a prevalence estimate.

The family/asset/kind tuples changed for **102 of 139 transferred records**. This includes refinements, additional components and conservative removal of assumptions; it is not an error-rate measurement against independent truth. The local comparison artifact preserves the old state and change counts, while the original transfer remains untouched.

Examples of corrected distinctions, without reproducing private complaint text:

- New streetlight provision, restoration of removed equipment, outage and switching faults remain distinct. An unspecified pole is not automatically a streetlight.
- Waste accumulation, missed collection, street sweeping and alleged collector conduct receive separate components where described.
- Road or footpath damage differs from absent paving, repair requests and obstruction. Figurative comparisons do not establish a collapsed bridge.
- An unspecified water leak retains an unknown family/source. Explicit drinking-water or named supply-pipeline descriptions can support a water-service proposal. A damaged pipe without reported escape does not acquire a leakage label.
- Odor does not establish drain blockage, and vegetation in a drain does not establish failed flow. Generic locations, conflicting statements and destroyed text are retained as uncertain/unusable, not forced into other.
- Private premises, compensation demands, alleged misconduct and regulatory questions can remain scope-review cases even when a physical component is described.

## Evidence and limitations

Each issue stores Unicode-character offsets into the pilot text, the proposed family/asset/kind and the basis `complainant_report_not_verified_event`. Supporting passages were selected by the assistant after reading the description. These offsets prove where the cited words occur, not that the proposed interpretation is true or the reported event occurred. No real severity, urgency, disease causation, crime or legal responsibility is verified.

Setting and time-state fields remain **unknown in this pass**. They were not systematically annotated; contextual remarks in rationales are not a completed ownership/time dataset. The new validator requires separate evidence if these fields are populated later. Asset vocabulary and family/asset compatibility are versioned in `issue_annotations.py`; active taxonomy v1 and the application do not change.

The pass uses the existing draft issue kinds, so urination, burning and odor can have a known family with unknown kind. This exposes a vocabulary limitation rather than inventing a new class silently. Scope and clarification outcomes can still contain useful components. An issue's presence in this artifact does not make it eligible for training or evaluation.

The 271-task pilot was selected for review coverage, not representative sampling. Family counts are nonexclusive AI proposals, not class support for the full corpus, model accuracy, Bengali/West Bengal coverage or all-India performance. Some proposed families have only one or two pilot records. The prior privacy proposals and unresolved holds remain separate and unchanged. No privacy clearance, independent reference labels, trained model or approved split is created.

[Label Studio's prediction documentation](https://labelstud.io/guide/predictions.html) separates pre-annotations from subsequent review/correction. We preserve that distinction, maintain the original predictions and store this assistant-authored pass separately. No external annotation service or new package was installed.

## Restricted artifacts and reproduction

- Final authored ledger: ignored `data/review/issue-text-authored-v2/annotations.json`, SHA-256 `f90086387ef94f0cdef9cf900a442a6c2c7d7260ba103fdd3dcf65134bed75b7`.
- Final validated output: ignored `data/review/issue-text-validated-v2`, containing annotations, per-record comparison, summary, hashes and COMPLETE.
- The initial v1 authored/validated artifacts are retained. A consistency check refined six records: traffic-signal mechanism, ambiguous pipe service, unspecified dumping material, parking ambiguity, streetlight switch repair and an uncertain meter-adjacent leak point. v2 is the final checkpoint; v1 is not overwritten or a second independent review.
- Private descriptions, evidence selections and per-record rationales stay outside Git. The public code/tests contain only synthetic fixtures and aggregate documentation.

The validator checks exact pilot coverage, unique identities, indexed input hashes and text hashes; allowed fields/vocabularies; family/asset compatibility; nonempty, bounded and nonoverlapping evidence spans; explicit unknown context; outcome consistency; and false training/privacy/independent-reference approvals. It rejects output overwrites and input nesting, and retains INCOMPLETE on failed writes. It does not authenticate deliberately rewritten indexes or prove semantic entailment/annotation accuracy.

Actual command, exit 0:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.issue_annotations --pilot data/interim/label-pilot-v1 --draft data/review/issue-description-draft-v1 --annotations data/review/issue-text-authored-v2/annotations.json --output data/review/issue-text-validated-v2
```

Use a fresh output directory when rerunning. Validation reproduces checks of locally authored judgments, not an independent reannotation. Private input artifacts are not present in a fresh clone.

Verification: **33 new contract tests passed in 3.38s**, then **206 research tests passed in 20.23s**:

```powershell
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-text-annotations-final
```

Tests cover complete/duplicate/missing records, stale input/text hashes, Unicode offsets, overlapping/empty evidence, unsupported labels and asset combinations, context evidence, ambiguous fluid sources, forbidden severity/event/human approval claims, deterministic output, original input preservation and interrupted writes. These are validation tests, not model-accuracy measurements. Application tests/builds were not rerun because the application and dependencies are unchanged.

Original OpenCity SHA-256 rechecked: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Prior AI response hash remains `480611baaa909cce2c7dfaba2f5b3be7c7b5df82744027f53cf9218b2ad4ff3c`; corrected privacy input remains `014aec50ef9251a25c7cb85990980af5fa1a09c3939c7a6710a7a339f794c952`. Source labels, original text, groups and unassigned splits remain intact.

## Next intended step

Follow-up completed: [Baseline readiness](BASELINE_READINESS.md) now reports candidate/class/group/privacy support and the predeclared evaluation protocol. Next implement the offline runner with synthetic fixtures and an explicit real-data gate. The annotation pass described here is complete; no training approval follows from it.

Produce a baseline-readiness assessment from these actual annotations: distinguish clear single-component candidates from mixed/ambiguous/scope cases, examine proposed class support and duplicate/privacy exclusions, and predeclare the text-baseline evaluation protocol. Do not repeat this completed 271-record pass as new work. Independent reference adjudication and rights/privacy/split approval remain explicit prerequisites to a validated training/evaluation release; AI-authored labels cannot serve as independent ground truth.
