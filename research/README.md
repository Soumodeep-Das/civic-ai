# CivicAI research workspace

This directory contains version-controlled research definitions and validation code. It does not contain an approved research dataset or measured results.

## Validate a manifest

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

The 70/15/15 targets are component assignment probabilities, not guaranteed ratios or class balance. Missing support and source/category distribution are reported. `training_approved: false` requires source, annotation, privacy, near-duplicate and sample-adequacy review. See `docs/ISSUE_006_DATA_PREPARATION.md` for evidence and the outstanding acquisition gate.

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
- `tests/`: automated validator tests.
