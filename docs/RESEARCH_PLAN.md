# Research Plan

## Aim

The minor-project study will evaluate how input modality affects classification of urban civic complaints. It must report only results produced by documented, reproducible experiments on traceable data.

## Research questions

### RQ1 Text-only classification

How effectively can complaint descriptions classify records into the agreed civic issue taxonomy?

A simple, interpretable baseline such as TF-IDF with logistic regression should be evaluated before a transformer model is considered.

### RQ2 Image-only classification

How effectively can complaint images classify records into the same taxonomy?

Transfer learning is the expected starting point. The final architecture depends on data volume, label compatibility, compute, and whether the task is image-level classification or object detection.

### RQ3 Multimodal classification

Does combining aligned text and image evidence improve classification over either modality alone under the same dataset split and label taxonomy?

Fusion design must be documented. A multimodal model is not assumed to outperform unimodal baselines; that is the question being tested.

### Priority mechanism in the approved prototype

The approved synopsis includes a separate transparent priority engine using a documented annotation and scoring procedure for severity and contextual priority. Evaluation is conditional on having sufficient defensible labels. This component must not use model confidence as a substitute for urgency, and it must allow human verification or correction.

### Future research Context-aware prioritization

A later major-project study may ask whether learned spatial, temporal, severity, recurrence, and other contextual features improve priority prediction or ranking beyond content-only inputs. The target definition, ethical implications, annotation process, and evaluation method must be established before making research claims.

## Experimental controls

- Freeze a versioned label taxonomy and inclusion criteria before the final experiments.
- Create one group-aware or source-aware split where needed to prevent near-duplicate or location leakage.
- Keep the final test split untouched during model and hyperparameter selection.
- Use the same eligible examples and split identifiers across modality comparisons, with missing-modality handling reported explicitly.
- Fit preprocessing only on training data.
- Record random seeds, code revision, environment, dataset version, preprocessing, hyperparameters, hardware, and run time.
- Store machine-readable predictions for error analysis without exposing restricted data.

## Baseline philosophy

Start with defensible simple baselines. Increased model complexity is justified only when it answers a research question and can be evaluated fairly. Candidate baselines include a majority-class predictor, TF-IDF plus a linear classifier for text, and a pretrained compact vision backbone with a replaced classification head for images.

## Evaluation

Because class imbalance is likely, the primary classification metric is expected to be macro-averaged F1. Also report per-class precision, recall, F1, support, a confusion matrix, and overall accuracy. Weighted F1 may be supplementary but must not replace per-class analysis.

If probabilities are used operationally, assess calibration with an appropriate method decided before final evaluation. Any confidence intervals, significance tests, or repeated-run summaries must state their procedure and assumptions; none are currently claimed.

## Ablation and error analysis

At minimum, compare text-only, image-only, and text-plus-image systems on the same held-out examples. Further ablations may examine fusion choice or removal of one modality if sample size permits.

Error analysis should use a predeclared sample or all test errors and examine ambiguous labels, poor-quality images, vague text, conflicting modalities, class imbalance, duplicates, and source artifacts. Conclusions must distinguish observed evidence from speculation.

## Reproducibility outputs

Each accepted experiment should produce:

- an immutable run identifier and Git commit
- dataset manifest/version and split identifiers
- configuration and environment record
- metrics and per-example predictions
- plots generated from saved results
- a short result note including failures and limitations

Large artifacts and restricted datasets remain outside Git; checksums and retrieval instructions should be committed when licensing permits.

## Literature and claims

Literature searches, citations, and venue/indexing claims require source verification. Dataset licenses and permitted uses must be checked at the source. No paper section may contain placeholder numbers that could be mistaken for measured results.
