# Issue #5 — Research data and taxonomy foundation

## Goal

Create the smallest defensible foundation for the later text, image and multimodal classification experiments. This issue freezes category taxonomy version 1, defines human annotation rules, records source/provenance requirements, and validates dataset manifests before any model can consume them.

This issue does **not** acquire a dataset, label real records, train a model, expose ML inference, or report metrics.

## Evidence used

- [Swachhata integration FAQ](https://www.swachh.city/assets/files/Integration_FAQ_V2.pdf): the official MoHUA platform uses explicit complaint categories and category-specific workflows. We use it as an Indian civic-domain reference, not as a dataset or a claim that CivicAI's taxonomy is identical.
- [Swachhata Engineer 2.0 manual](https://www.swachh.city/assets/files/Swachhata-Engineer2.0-User-Manual.pdf): complaint records combine a description, picture and accurate location. CivicAI already collects these application fields, but application records do not automatically become research data.
- [NYC311 Open Data update](https://www.nyc.gov/opendata/news/all-news/311-Service-Requests-Updates): large civic datasets evolve, rename fields and span many problem types. Any adopted source therefore needs a pinned extraction date, source schema and mapping—not a silent live download.
- [Datasheets for Datasets](https://arxiv.org/abs/1803.09010): dataset motivation, composition, collection, intended use, distribution and maintenance should be documented.
- [NIST AI RMF Playbook](https://airc.nist.gov/docs/AI_RMF_Playbook.pdf): provenance should cover sources, transformations, labels, dependencies, constraints and metadata; data should be adequate and limited to the stated purpose.
- [scikit-learn group-aware splitting](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html): groups, rather than individual samples, are the unit of separation where related records could leak across splits.

## Accepted scope

1. Version the eight-category working taxonomy as `civicai-category-v1`.
2. Define inclusion, exclusion, multi-issue, ambiguity, image/text-conflict, privacy and adjudication rules.
3. Define a strict JSON Lines manifest that references restricted text/image files without embedding them in Git.
4. Validate schema, category/status consistency, safe relative references, unique IDs, source identity, group leakage and exact-hash leakage.
5. Optionally verify referenced files and SHA-256 hashes against an explicit data root.
6. Include a clearly synthetic manifest example solely to test the contract.

## Explicit exclusions

- No downloaded or scraped civic dataset.
- No claim that any candidate source is licensed or suitable until its terms and mapping are separately approved.
- No real complaint text, image, coordinate or personal information in Git.
- No severity or priority labels; those require separate rubrics and must remain distinct from category.
- No random train/test splitting, augmentation, feature extraction, training or evaluation.
- No application database migration or API/frontend change.

## Acceptance criteria

- Taxonomy v1 contains exactly the eight approved working categories with clear boundaries.
- Annotation guidance explains how to handle multiple issues, uncertainty, `other`, exclusions and disagreements.
- A valid synthetic manifest passes the validator.
- Invalid category/status combinations, unsafe paths, duplicate identities, group leakage and exact-content leakage fail with line-specific messages.
- Optional file verification rejects missing files and checksum mismatches.
- Tests and documentation pass without adding a new runtime dependency.

## Deferred risks

Near-duplicate image/text detection, inter-annotator agreement measurement, stratified group split generation, dataset acquisition and license approval remain future work. Exact hashes cannot detect paraphrases, crops or visually similar events. The taxonomy may require a version 2 after real-source feasibility review; version 1 labels must never be silently reinterpreted.
