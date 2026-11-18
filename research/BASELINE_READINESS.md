# Text baseline readiness assessment

2026-11-18. This is a completed assessment and proposed experiment protocol, **not a training release or model result**. It uses the text-grounded AI annotations, corrected privacy recommendations, original pilot group keys and proposed near-duplicate containment. No labels, source files, application behavior or original groups/splits were changed.

## Candidate selection

For the first family-classification study, a candidate must have outcome `described_issue` and exactly one known service family. Several components in that same family remain one complaint. A collection failure plus dumped waste can therefore stay a solid-waste candidate; a road defect plus sewer overflow is deferred instead of forced into one label. Conflicting or uncertain linked records require group review before candidacy. This is an experimental target proposal, not an adopted taxonomy or automatic municipal routing rule.

| Disposition | Records |
|---|---:|
| Single-family AI annotation candidate | 157 |
| Multiple service families | 33 |
| Clarification required | 61 |
| Scope review required | 16 |
| Unusable text | 4 |
| Total | 271 |

The 157 candidates include 129 single-component and 28 same-family multiple-component descriptions. This explains the increase over the earlier 129 figure without inventing additional records. No candidate is silently deleted or relabeled as other. The pilot was designed for annotation coverage, not representative sampling; these proportions are not citywide prevalence or expected production coverage.

## Proposed family support

The analysis constructs conservative containment components from existing proposed groups plus the reviewed duplicate links **before filtering**. It includes transitive links through deferred records. A component is a planning constraint, not a verified independent incident. The near-text pair stays together, reducing 271 pilot records to 270 components and 157 candidates to 156 components. No original group or split assignment was changed.

| Family | Candidate records | Containment components | Meets planning floor |
|---|---:|---:|---|
| Roads and pedestrian access | 48 | 48 | Yes |
| Solid waste | 31 | 31 | Yes |
| Public lighting | 29 | 28 | Yes |
| Drainage and sewerage | 26 | 26 | Yes |
| Mobility and traffic infrastructure | 7 | 7 | No |
| Water services | 6 | 6 | No |
| Sanitation and public health | 5 | 5 | No |
| Animals | 2 | 2 | No |
| Electricity services | 1 | 1 | No |
| Pollution and nuisance | 1 | 1 | No |
| Public assets and space | 1 | 1 | No |
| Parks, trees and waterbodies | 0 | 0 | No |

**Proposed first development scope: four families, 134 records, 133 containment components.** The planning floor of 20 components per family is an explicitly chosen engineering floor for a small three-fold development study, not a power calculation, proof of independent scenes, or sufficient production evidence. It was specified before any model fitting. Count support must be recalculated after reference/privacy review; a family can lose candidates. No result exists yet to justify a release threshold.

The other 23 candidates and 114 deferred records remain in the inventory. Broader CivicAI reporting is unchanged. Rare families need additional annotation/coverage, not synthetic incident multiplication, random duplication or merging into other to improve a score. No all-India, West Bengal, Bengali-language or image-model capability follows from this Bengaluru text pilot.

## Privacy and reference gates

Within the 157 candidates, current privacy flags are:

- 21 with proposed redaction spans;
- 16 with sensitive-context holds;
- 55 with retention proposals that are not clearance;
- 65 without completed contextual privacy review in that earlier pass.

These flag types are reported as potentially overlapping; this snapshot's counts sum to 157. Removing a name alone does not resolve allegations, linkage risks or the rest of a record. The readiness tool does not apply masking or promote any privacy status.

**Training-eligible records: zero under the current release gates. Independent reference records: zero.** All labels remain assistant-authored proposals. Rights/derivative release, privacy, independent reference adjudication, full-corpus event grouping, target adoption and a genuinely untouched independent evaluation set remain outstanding. This finding does not invalidate the engineering/annotation work; it prevents reporting agreement with AI labels as real-world accuracy.

## Evaluation protocol specified before fitting

The machine-readable proposal is [protocols/text_baseline_v1.json](protocols/text_baseline_v1.json). It is a protocol specification, not an implemented training runner or approval.

1. **Task/input:** classify the single service family from approved complaint text. Do not use source tags, IDs, annotation rationales/evidence, coordinates, group IDs or privacy flags as features. Keep unknown/mixed/scope cases in a separately reported challenge set; do not manufacture a dominant ground-truth label.
2. **Baseline/model:** most-frequent-class dummy comparator, then word unigram/bigram TF-IDF plus logistic regression. Preserve negation; no English stop-word deletion or accent stripping. Parameters, six candidate C/weight combinations and deterministic tie-breaking are recorded in JSON. No transformer or external AI service is needed for this first experiment.
3. **Development:** three-fold stratified grouped validation, seed 42. Related records stay together. Check actual per-class support in every train/validation fold before fitting; a splitter's name does not guarantee feasibility. Stop on missing classes rather than quietly dropping them or reverting to random row splitting. Fit TF-IDF vocabulary/IDF only inside each training fold. Report selection-fold metrics as development evidence, never an untouched test score.
4. **Independent test:** the current 271-record pilot has already shaped definitions and is **never the final test set**. Acquire/reference-review new Indian groups, establish disjointness from all pilot/development components and freeze the test manifest before fitting the final model. A planning minimum of 20 independent test groups per selected class is only a small descriptive floor, not statistical sufficiency or production certification. Do not create a smaller convenient test after observing model results.
5. **Measures:** fixed-label macro-F1, per-class precision/recall/F1/support, confusion matrix, balanced accuracy, group/record coverage and all deferral counts. Use zero-division handling explicitly and report missing-class conditions. For an eligible independent test, predeclare 2,000 reference-class-stratified group bootstrap replicates, seed 42, for 95% intervals; resample groups rather than correlated rows. Neither intervals nor point estimates establish national generalization.
6. **Limits:** the first study is closed-set on eligible scope. Do not treat maximum probability as calibrated confidence or claim it can detect unsupported complaints. No abstention cutoff, severity score, priority score, automatic routing or operational acceptance threshold is implemented. Any subsequent threshold/abstention study needs reference data and validation separate from the final test.
7. **Provenance:** record exact library versions, Git revision, input/split hashes, seed, hardware, parameters, convergence warnings, runtime, raw predictions, fold metrics and exclusion counts. Convergence failures are unresolved runs, not silently accepted results. A weak-supervision experiment using AI labels requires a separate explicitly disclosed protocol; it does not replace independent evaluation.

Primary guidance: [scikit-learn grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data) explains group separation; [its leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) supports train-only preprocessing; [F1 documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) defines macro averaging and zero-division handling. The project-specific floors, candidate policy and model search above are our proposed design choices, not requirements attributed to those sources.

## Implementation and verification

`baseline_readiness` revalidates annotations, verifies indexed inputs, matches pilot/text/privacy/group identities, rejects inconsistent approval claims and creates a private per-record inventory plus aggregate support/summary and a protocol snapshot. It records candidate group conflicts and uncertainty instead of splitting linked records. It is read-only with respect to all inputs, creates no train/test split and refuses output overwrite/input nesting. Hash indexes detect accidental changes, not a maliciously rewritten provenance chain. Source licensing and semantic correctness are not verified by this command.

Actual command, exit 0:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.baseline_readiness --pilot data/interim/label-pilot-v1 --draft data/review/issue-description-draft-v1 --annotations data/review/issue-text-validated-v2 --context data/review/context-review-validated-v1 --output data/review/baseline-readiness-v2
```

Use a fresh output path for a rerun. `data/review/baseline-readiness-v2` is ignored; it contains `inventory.json`, `support.json`, `summary.json`, `protocol.json`, hashes and COMPLETE. The initial v1 is preserved; v2 incorporates stricter privacy consistency checks and the clarified class-stratified group bootstrap specification. Counts are unchanged. No private text or identities are committed.

**22 new tests passed in 2.03s; all 228 research tests passed in 21.58s** using `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-baseline-readiness-final`. Tests cover same-family components, transitive links through excluded rows, conflicting source groups, counts by group, privacy risks, exact input bindings, forbidden approvals, holdout misuse, immutable/deterministic outputs and interrupted writes. No model dependency was installed. Application tests/builds were not rerun because runtime code and dependencies are unchanged.

Raw OpenCity checksum reverified: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. All individual proposals, originals and existing groups remain intact. No training result or performance claim is made.

## Next intended implementation

Implement the reproducible offline baseline runner from this protocol, using synthetic fixtures to verify group separation, training-only preprocessing, metrics and artifact provenance. Keep real-data execution gated on an explicit reviewed release; do not turn this private candidate inventory into a training manifest automatically. Reference/privacy/rights work remains necessary alongside that implementation. No application inference integration starts yet.
