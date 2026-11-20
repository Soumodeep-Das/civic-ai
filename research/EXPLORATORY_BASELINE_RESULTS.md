# First exploratory real-text baseline

2026-11-19. Actual local fit completed on 97 screened Bengaluru descriptions (40 roads/footpaths, 21 waste, 18 drainage, 18 lighting); 37 of 134 candidates deferred. Labels and privacy screening are AI-authored, not independent reference review. This is not a production or certified privacy release.

Three grouped development folds, six TF-IDF/logistic-regression configurations and a majority-class comparator. Selected C=0.1, balanced class weights. Mean development macro-F1: 0.8643655078; dummy: 0.1434407096. These are selection-set agreement metrics against AI labels, not independent accuracy, calibrated confidence or municipal effectiveness. Small per-fold class counts and selection on the same folds limit interpretation. No West Bengal, image, multilingual or severity performance demonstrated.

The exploratory planning floor was explicitly revised from 20 to 18 groups before fitting; the original independent-reference protocol remains unchanged. Source-specific publisher metadata identifies CC BY-SA 2.0. Attribution: OpenCity/Janaagraha iCMyC; retained catalogue author Vaidyanathan R.; resource credits Vivek Mathew and Haji Shariefullah. Local restricted exploration only; no raw data, derived text or model distribution. Privacy screening is not anonymity certification.

Command: `python -m research.civicai_research.exploratory_fit`. Fixed input snapshot and output: ignored `research/results/exploratory-ai-labels-v1`. Raw predictions, folds, protocol, versions, input hashes, timings and selected model saved. Failed writes retain INCOMPLETE; existing output refused. The synthetic runner and human-reviewed export gate are unchanged. No live inference enabled.

Next: inspect out-of-fold disagreements and unsupported-input behavior, harden/test the dedicated experiment loader, then integrate a guarded experimental assessment with municipal review. The fixed experiment script is not a general approved-release loader.

Selected configuration has 13 out-of-fold disagreements among 97 records; these are disagreements with AI proposals, not confirmed model errors.

## Error review and challenge probes

Read all 13 out-of-fold disagreements. Failures include short/rare wording (dustbins, absent footpaths, open manholes), road-versus-drain context and debris on pedestrian routes. Some labels have plausible overlapping interpretations; no labels were changed to improve scores. Seven authored challenge probes were evaluated against the final refit; these are not independent test observations. The classifier always returns one of four families, even for unrelated input, negated/resolved issues, mixed issues and unsupported script. Zero-vocabulary inputs also receive a class. Therefore raw predictions must not be exposed as reliable classification. A guarded assessment needs explicit unsupported/insufficient-evidence handling and staff review; confidence thresholds alone cannot prove out-of-scope detection.

Hardened the fixed experiment loader against duplicate/missing decisions, stale actual text, altered provenance and unresolved holds. Existing model artifacts retain their original implementation hash; this change does not retroactively rebind the earlier run. Challenge artifacts are separate diagnostics. A console encoding failure occurred after the UTF-8 probe file was saved; the saved result was subsequently read using escaped output.
