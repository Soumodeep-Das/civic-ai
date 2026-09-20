# Data Specification

## Status

The broad canonical record below includes future proposals. The implemented application fields are complaint_id, description, latitude, longitude, image_ref, status, created_at and updated_at; no research dataset is claimed.

Migration 0002 adds nullable VARCHAR(200) image_ref to migration 0001. Existing records remain with null image_ref. Images are local runtime files; only their relative serving URL is stored in PostgreSQL. Coordinates remain independently optional DOUBLE PRECISION values with range constraints. They are metadata only, excluded from the current text/image/multimodal classification experiment. No location_accuracy_m or reporter_id field is implemented.

## Canonical complaint record

| Group | Field | Type or form | Purpose |
|---|---|---|---|
| Identity | `complaint_id` | UUID | Stable internal identifier |
| Application | `description` | text | Citizen-provided complaint text |
| Application | `image_ref` | nullable URI/key | Reference to submitted image |
| Application | `latitude`, `longitude` | nullable decimal | Submitted or selected location |
| Application | `location_accuracy_m` | nullable decimal | Accuracy when available |
| Application | `status` | controlled value | Workflow state, not an ML label |
| Application | `created_at`, `updated_at` | UTC timestamp | Record lifecycle |
| Application | `reporter_id` | nullable identifier | Account link; excluded from research by default |
| Annotation | `category_label` | controlled value | Human reference label for classification |
| Annotation | `severity_label` | nullable controlled value | Human assessment under a written rubric |
| Annotation | `priority_label` | nullable controlled value | Operational target under a written rubric |
| Annotation | `annotator_id` | pseudonymous identifier | Annotation provenance |
| Annotation | `annotation_version` | string | Guideline/taxonomy version |
| Annotation | `annotation_notes` | nullable text | Ambiguity and adjudication notes |
| Provenance | `source_name` | string | Origin of the record or component |
| Provenance | `source_record_id` | nullable string | Source traceability without assuming ownership |
| Provenance | `license_or_terms` | string/reference | Known usage condition; must be verified |
| Provenance | `consent_or_basis` | nullable string | Collection basis where applicable |
| Dataset | `dataset_version` | string | Version of curated release |
| Dataset | `split` | train/validation/test | Frozen experiment assignment |
| Dataset | `group_id` | nullable string | Keeps duplicates/related examples in one split |
| Dataset | `text_available`, `image_available` | boolean | Modality availability |
| Prediction | `model_version` | string | Model provenance |
| Prediction | `predicted_category` | controlled value | Model output, never the ground truth field |
| Prediction | `category_confidence` | nullable decimal | Calibrated or raw score, clearly identified |
| Prediction | `inferred_at` | timestamp | Prediction provenance |

## Application fields versus research data

Application records exist to deliver a workflow. Research datasets require additional provenance, verified usage rights, de-identification, quality checks, labels, frozen splits, and versioning. A production record must not automatically enter a research dataset.

Coordinates, free text, images, and reporter identifiers may contain personal or sensitive information. Data minimization, access control, redaction, retention, and consent/legal basis must be decided before real submissions are collected for research.

## Taxonomy rules

The working categories are listed in `PROJECT_CONTEXT.md`. Before annotation, create a versioned guideline with positive and negative examples, boundary cases, handling for multiple issues, the definition of `other`, and an adjudication process. A category change creates a new taxonomy version and may require relabeling.

Severity and priority require separate rubrics. Priority must not be backfilled from category through a fixed lookup and then presented as independently annotated evidence.

## Quality checks

- Validate required fields, encoding, timestamps, coordinate ranges, and media readability.
- Detect exact and near duplicates before splitting.
- Prevent the same source event, location burst, or augmented derivative from crossing splits where it would cause leakage.
- Track missingness rather than silently imputing it.
- Audit class and source distributions across splits.
- Use independent annotation and adjudication on a meaningful subset if resources permit.
- Report exclusions and transformations with counts.

## Storage and versioning

Raw data is immutable and access controlled. Derived data should be reproducible from raw inputs plus versioned transformation code. Git stores schemas, manifests, small non-sensitive samples, checksums, and documentation—not unrestricted raw media or large model-ready datasets.

## Unresolved data decisions

- Which sources are available and licensed for this taxonomy?
- Will each record have aligned text and image, or will modalities be partially missing?
- What is the unit of grouping for leakage-safe splits?
- Who may annotate, and how will disagreements be resolved?
- What severity and priority definitions can be defended?
- What minimum class support is feasible without fabricating or over-augmenting data?
