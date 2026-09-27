# Issue #6 — Dataset suitability and reproducible preparation

Status: preparation tooling implemented; source approval/acquisition and a real frozen evaluation dataset remain incomplete. No model training is authorized by a successful preparation run alone.

## Source assessment (2026-09-27)

| Source | Evidence and suitability | Decision for the planned eight-category paired study |
|---|---|---|
| [NYC311 official update](https://www.nyc.gov/opendata/news/all-news/311-Service-Requests-Updates) | Problem and Problem Detail are category hierarchy fields; Additional Details is a subset. These are not established as independent citizen narratives. | Do not construct input text from label fields or resolution outcomes. No aligned image source verified. Not approved. |
| [RDD2022 authors](https://github.com/sekilab/RoadDamageDetector) | Road images and bounding-box annotations; authors state CC BY-SA 4.0 for images. India subset exists. Test images lack public labels. | Candidate auxiliary road-image source only. Requires retained rights evidence, mapping and scene/group review. Does not cover eight classes or paired complaint text. No archive downloaded. |
| [TACO authors](https://github.com/pedropro/TACO) | Litter images with segmentation annotations, hosted on Flickr; unofficial annotations are explicitly unreviewed. | Candidate auxiliary waste-image source only. Repository software license is not treated as proof of every image's reuse terms. No paired narratives established. |
| [IChangeMyCity AWS registry](https://github.com/awslabs/open-data-registry/blob/main/datasets/ichangemycity.yaml) | Indian civic complaints; registry marks distribution deprecated and no longer provided through that mechanism. | Availability and current terms unresolved. Do not rely on the historical bucket as an acquired dataset. |
| [CESAMARD authors](https://github.com/appy1608/EMNLP2023-Multimodal-Complaint-Detection) | Paired review text/images with complaint, sentiment and emotion labels. | Those targets do not establish CivicAI incident categories. No direct mapping accepted. |

These checks do not prove that no suitable public dataset exists. They establish that the inspected sources cannot currently support the promised comparison. No source is approved or acquired in this checkpoint. The Figshare RDD page/API could not be fetched through the research tool; no unseen license details are asserted.

The important experimental risk is source/category confounding: combining all road examples from one collection and all waste examples from another can make camera style predict the category. Such a mixture cannot alone establish generalization to local citizen complaints. Never pair unrelated text and photos just because their category names match, and never use generated captions as genuine citizen descriptions for the primary comparison.

## Implemented contract

`research.civicai_research.prepare` imports a local Issue #5 manifest and verifies every referenced file against its SHA-256. It preserves raw files in place. It checks UTF-8 nonempty text (up to 1 MiB) and decodes single-frame JPEG/PNG images (up to 25 million pixels). It requires a single dataset version and refuses existing split assignments and existing output directories.

It forms connected components using original event groups, exact modality bytes, normalized text (Unicode NFKC, case folding, collapsed whitespace), and identical decoded RGB pixels after EXIF orientation. Connections are transitive. Conflicting labels or disputed members keep the entire component unassigned. Pending/excluded records remain unassigned. Paired mode is the default, so all later modality comparisons can use the same eligible records. Explicit unpaired mode is only a separate feasibility proposal.

Each component is assigned using a SHA-256 seed/key bucket with target probabilities 70%/15%/15%. This is deterministic and row-order independent, not stratification and not a guarantee of exact ratios or class coverage. Small datasets and large components may leave a split/class empty. The report exposes missing classes, record counts, independent component counts, source/category counts and exclusions. Do not retry seeds based on model performance. After review, freeze the chosen proposal and predeclare any redesign before looking at test predictions.

The output contains a new manifest and report, published together from a temporary directory. The report records input/output/taxonomy/code hashes, seed, algorithm and Python/Pillow versions. `training_approved` is always false: this tool produces a proposal, not a rights or quality approval. Raw data must remain immutable; content is rechecked before publication. JSON files use stable ordering and LF newlines.

Design reference: [scikit-learn cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html) discusses keeping dependent groups separated and the difference between grouped and stratified evaluation. We use a dependency-free component assignment and explicitly report its limitations.

## Remaining acceptance gates

- Acquire a suitable source with retrievable version, license/terms evidence and a completed datasheet.
- Establish genuine incident-level text/photo alignment and human category annotations.
- Review privacy, ambiguous cases, near duplicates, related scenes and language coverage.
- Choose an adequate independent sample size per class; mere presence in each split is insufficient.
- Review source confounding, lock a split and retain provenance before training.

Exact/normalized duplicate checks do not detect all crops, recompressions, paraphrases or repeated locations. Human review or a separately validated near-duplicate audit must occur before acceptance. No metadata field can automatically prove consent, label correctness or representativeness.

## Proposed collection route for review

If no approved paired source is available, begin a small original local feasibility collection: an actual issue photo plus a independently written description of the same incident, with source/basis recorded and unnecessary personal details removed. Start by checking whether all eight categories can be collected and distinguished; do not promise a performance target or designate a tiny pilot as the final test set. Two people should independently label a subset and record disagreements for adjudication. Related views of one incident share one event group.

This requires the user's access to real observations or an institution/provider dataset. No outreach, collection consent, or human annotation has been invented or performed by the agent. The next decision is the acquisition route, not a model architecture.
