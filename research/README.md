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

## Layout

- `taxonomy/category_v1.json`: machine-readable category identifiers and boundaries.
- `ANNOTATION_GUIDELINES_V1.md`: human labeling and adjudication rules.
- `DATASET_DATASHEET_TEMPLATE.md`: questions that must be answered for an accepted dataset version.
- `SOURCE_REGISTER.md`: source candidates and approval state.
- `examples/manifest.synthetic.jsonl`: non-data contract example.
- `civicai_research/manifest.py`: strict manifest and leakage validator.
- `tests/`: automated validator tests.
