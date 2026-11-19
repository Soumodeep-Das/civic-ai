# Offline text baseline runner

2026-11-19. Implements the **synthetic-only engineering stage** of [the text baseline protocol](protocols/text_baseline_v1.json). The command trains actual estimators on a built-in toy fixture to exercise the workflow; it does not train or evaluate a CivicAI model on real Indian complaints.

## What runs

The built-in fixture contains 160 authored sentences, four families, 80 artificial groups and two related descriptions per group. These are synthetic test cases, not collected incidents, independent scenes or an Indian research dataset. Distinct sentinel words support leakage tests; easy repeated templates intentionally exercise plumbing, not realistic generalization.

The runner implements:

- Input checks for empty/oversized text, repeated IDs, conflicting labels within a group, undeclared fields and normalized duplicate text crossing groups.
- Three deterministic stratified grouped folds with seed 42. Every record is validated exactly once; actual partitions must have disjoint groups, complete record coverage and every selected class on both sides. A missing class stops the run rather than silently changing the study.
- A most-frequent-class dummy comparator fitted separately on each training fold.
- Word unigram/bigram TF-IDF and logistic regression using the six C/class-weight combinations predeclared in protocol v1. Each candidate/fold fits a fresh pipeline on training text only. Validation vocabulary and IDF never enter training. Negation is retained; tokenization/language behavior is not evaluated on real Indian-language text here.
- Fixed-label macro-F1, per-class precision/recall/F1/support, confusion matrices and balanced accuracy. Undefined predicted-class precision is explicitly zero. Selection uses mean development-fold macro-F1, then smaller C, then no class weighting. These selection scores are not independent test scores.
- An all-synthetic-development-data refit of the selected model, clearly marked as a synthetic artifact. No final test metrics are produced by that refit.
- Failure on convergence warnings or invalid training vocabulary. Failed fitting/writing retains INCOMPLETE; a partial model is never marked COMPLETE.

Numerical work uses one thread. Runs record exact package/Python versions, platform/architecture/CPU count, seed through the protocol, source/protocol/input/split hashes, Git revision and dirty state, elapsed/UTC times, warnings, parameters and coverage. Data/splits/predictions are reproducible under the tested environment; timing/Git metadata differ between runs and identical floating-point behavior across machines is not promised.

## Real-data gate and boundaries

The CLI accepts only the built-in fixture through `--synthetic`. `--release` is a reserved, **always-refused** path: it is rejected before reading the file or importing a fitting library. A JSON file claiming approval cannot unlock real-data execution. There is no custom dataset-input option, no production database access and no loading of the ignored AI candidate inventory.

Internal Python functions exist for tests and are not an authorization/security boundary against someone modifying or importing the source code. The supported CLI has no real-data bypass. The reviewed-release loader, approved redaction/export path and independent reference dataset are still absent. This is intentional; the runner is not described as real-data-ready.

No production inference endpoint, automatic routing, severity/priority predictor, calibrated confidence, independent-test evaluator, bootstrap interval or challenge-set evaluator is implemented. Those parts of the broader protocol remain future work requiring suitable reviewed data. No prior raw complaints, annotations, privacy states, active taxonomy, groups or application behavior are changed.

## Setup and run locally

From the repository root, using Python 3.12 and the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test,research]"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-baseline-runner-local
.\.venv\Scripts\python.exe -m research.civicai_research.text_baseline --synthetic --output research/results/synthetic-baseline-local-v1
```

Use a fresh output name each time. Output must resolve inside ignored `research/results`. Existing outputs and paths outside that directory are refused. ML engine tests explicitly skip if the optional libraries are absent; the release-gate tests still run. CI installs `.[test,research]` so the full suite is exercised there; a local skipped ML module is not evidence that the engine passed.

The optional `research` extra pins scikit-learn 1.7.2, NumPy 2.2.6, SciPy 1.15.3, joblib 1.5.2 and threadpoolctl 3.6.0. These pins match the tested Python 3.12 environment and versioned API references; they are not a claim to be the latest releases. Base application dependencies and Docker install commands remain unchanged, so production images do not install this extra. The repository-root `research` package is executed with `python -m` from the checkout; it is not added to the backend wheel.

On this Windows agent host, editable backend rebuilding failed in temporary/build paths (first a setuptools temporary-path interpolation error, then WinError 3). For an **already configured backend virtual environment**, install exactly the declared research pins without rebuilding it:

```powershell
.\.venv\Scripts\python.exe -c "import subprocess,sys,tomllib; from pathlib import Path; deps=tomllib.loads(Path('pyproject.toml').read_text())['project']['optional-dependencies']['research']; subprocess.check_call([sys.executable,'-m','pip','install','--only-binary=:all:',*deps])"
```

This is the fallback used locally. It does not upgrade unrelated backend packages or alter machine-wide Python. No credentials or environment secrets are required.

## Local artifacts

The run creates `synthetic-fixture.json`, `protocol.json`, `split-plan.json`, `cv-results.json`, `predictions.json`, `synthetic-model.joblib`, `summary.json`, `artifacts.json` and COMPLETE. Each of seven evaluated configurations (dummy plus six linear candidates) has exactly one out-of-fold prediction per fixture record: 1,120 prediction entries. The model bundle is explicitly labeled `synthetic_smoke_model_not_for_deployment`, with real-data approval false. No application model loader is connected to it.

Keep these artifacts out of Git. The joblib file is a local trusted-output artifact, not a safe exchange format for arbitrary models. [scikit-learn's persistence guidance](https://scikit-learn.org/1.7/model_persistence.html) explains the execution risks of pickle/joblib loading and version compatibility. The command never loads a supplied model; tests reload only their own newly produced fixture artifact.

Primary design references: [grouped stratification](https://scikit-learn.org/1.7/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html), [train-only preprocessing and leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage), and the [pinned package's declared dependencies](https://pypi.org/project/scikit-learn/1.7.2/). Actual fold feasibility is checked rather than presumed from stratification.

## Next implementation

Implement the reviewed-release contract and privacy-safe export path, preserving independent-reference versus AI-proposed labels and enforcing rights, provenance, group and split approval. Do not enable the runner on the 134 AI-label candidates merely because the synthetic workflow passes. Any proposed weak-supervision experiment needs a separately disclosed protocol and cannot serve as independent accuracy evidence.

## Observed verification (2026-11-19)

Focused tests: **23 passed in 23.41s**. Full research suite: **251 passed in 28.58s**, with no skipped ML module, using `python -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-baseline-runner-confirmed`. `pip check` found no broken requirements.

The actual synthetic command succeeded at ignored `research/results/synthetic-baseline-2026-11-19-v1`: 160 records, 80 groups, three folds, six candidates plus dummy, 1,120 predictions and zero convergence warnings. Fixture SHA-256: `9595e91bf2566ac9e4fd8badb03817ddfc0f7eca73247a6a7884833362f30941`; split-plan SHA-256: `e73129d760ed443f0bdcac99ce3cbc53adcab31b2045ca07b80c11389980d505`. All saved artifact hashes and current implementation binding were checked. The run records its pre-commit revision and dirty state honestly.

A real-release CLI attempt exited 1 without creating output. Source OpenCity SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Base dependency equality against HEAD was checked; application tests/builds were not rerun because runtime code was unchanged. Remote CI execution is not claimed by these local results.
