# CivicAI research workspace

This directory contains version-controlled research definitions and validation code. It does not contain an approved research dataset or measured results.

## Validate a manifest

## Acquire Indian text data for curation

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.opencity --output data/raw/icmyc-india-v3
```

This retrieves a bounded (20 MiB maximum) publisher CSV and metadata snapshot. Output is ignored by Git and cannot overwrite an existing snapshot. Original bytes/checksums and decoding are recorded. Imported descriptions remain `pending` and `unassigned`; source categories are separate metadata, never input text or automatically claimed human reference labels. No photos are supplied by this source. Free text and the raw CSV require local privacy review before any release. `prepare` accepts only reviewed Indian sources. A country registry entry is not training approval.

An interrupted acquisition stays marked `INCOMPLETE`. Resume only its integrity gate—without another download—with:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.opencity --output data/raw/icmyc-india-v2 --verify-existing
```

Audit a completed snapshot into a new immutable ignored directory:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.audit data/raw/icmyc-india-v2 --output data/processed/icmyc-audit-v5
```

The audit reports missingness, simple text-quality/language-script/privacy signals, source distributions, coordinate/time coverage, duplicate risks and explicit proposed-mapping states. It emits review references, not raw text, and never approves training.

## Issue #7 Stage A human review

Generate the offline, ignored review package from the verified snapshot and audit:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.review create --snapshot data/raw/icmyc-india-v2 --audit data/processed/icmyc-audit-v5 --output data/interim/issue7-review-v5 --examples-per-group 3
```

The generated package contains blank CSV forms, checksums and reviewer instructions. It preserves provenance, escapes spreadsheet-leading source text, supports partial independent submissions, validates immutable context and decision-specific requirements, detects duplicate/conflicting reviews and produces an adjudication handoff. See `docs/ISSUE_007_HUMAN_REVIEW.md` and `research/review/README.md` for exact commands. No review decision or complaint preview is committed.

## Manifest validation

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.manifest research/examples/manifest.synthetic.jsonl
```

The synthetic example checks only the manifest contract; its records, paths and hashes are illustrative and are not training data.

To verify real referenced files and their SHA-256 hashes, keep the restricted dataset outside Git and supply its root explicitly:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.manifest C:\restricted\civicai\manifest.jsonl --data-root C:\restricted\civicai
```

The validator never downloads data. A successful validation means the manifest is internally consistent; it does not prove consent, licensing, representativeness, label correctness or research fitness.

## Prepare a reviewed local source manifest

Use actual locally available files; the Issue #5 illustrative paths/hashes cannot pass file verification:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.prepare data/raw/collection-v1/manifest.jsonl --data-root data/raw/collection-v1 --output data/processed/proposal-v1 --seed 42
```

Run from the repository root after the normal editable installation. Pillow is already an application dependency. The command verifies contents, connects event/exact/normalized duplicates, and writes an immutable split proposal and audit report under ignored `data/processed`. Use a new version directory for a new proposal; never overwrite a frozen release. `--allow-unpaired` supports a separate unimodal feasibility proposal. Inputs must all be unassigned and share one dataset version. Text and image data remain local. No download, source-field mapping or annotation is done by this command.

The 70/15/15 targets are component assignment probabilities, not guaranteed ratios or class balance. Missing support and source/category distribution are reported. `training_approved: false` requires source, annotation, privacy, near-duplicate and sample-adequacy review. See `docs/ISSUE_006_DATA_PREPARATION.md` for evidence and outstanding approval gates.

Tests (choose a fresh temporary directory if a prior run owns the example path):

```powershell
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-research-local
```

## Files

- `taxonomy/category_v1.json`: machine-readable category identifiers and boundaries.
- `ANNOTATION_GUIDELINES_V1.md`: human labeling and adjudication rules.
- `DATASET_DATASHEET_TEMPLATE.md`: questions that must be answered for an accepted dataset version.
- `SOURCE_REGISTER.md`: source candidates and approval state.
- `examples/manifest.synthetic.jsonl`: non-data contract example.
- `civicai_research/manifest.py`: strict manifest and leakage validator.
- `civicai_research/opencity.py`: bounded, checksum-pinned Indian source acquisition.
- `civicai_research/audit.py`: deterministic source audit and privacy-conscious review queues.
- `mappings/icmyc_v1.json`: proposed source-label mapping states; not gold labels.
- `review/review_schema_v1.json`: allowed human decision states and outcome fields.
- `civicai_research/review.py`: offline package generation, submission validation, merging and conflict/adjudication checks.
- `civicai_research/curate.py`: deterministic redaction and fail-closed Stage B readiness skeleton.
- `tests/`: automated validator tests.
