# Data Specification

## Status

The broad canonical record below includes future proposals. The implemented application fields are complaint_id, description, latitude, longitude, image_ref, location_label, location_precision, location_details, location_source, location_accuracy_m, status, created_at and updated_at; no research dataset is claimed.

Migration 0002 adds nullable VARCHAR(200) image_ref to migration 0001. Existing records remain with null image_ref. Images are runtime evidence files; only an internal relative API reference is stored in PostgreSQL. In production the files live in a private persistent volume and require municipal complaint authorization for retrieval. Coordinates remain independently optional DOUBLE PRECISION values with range constraints. They are metadata only and excluded from the current text/image/multimodal classification experiment. No reporter_id field is implemented.

Migration 0003 adds nullable location_label VARCHAR(300), location_precision VARCHAR(20) and location_details VARCHAR(500). Precision is controlled to exact, approximate or broad. New context requires both coordinates plus a label and precision; legacy coordinate-only rows remain valid. `exact` means the citizen confirmed a device position or map point, not a surveyed measurement. These fields are application metadata and remain excluded from the current classification experiment.

Migration 0004 adds nullable location_source VARCHAR(20) and location_accuracy_m DOUBLE PRECISION. Source is controlled to `search`, `device` or `map`. Accuracy must be finite, between 0 and 100,000 metres, and is valid only for a device source. Source/accuracy context requires coordinates, label and precision. Existing rows remain null and valid.

Migration 0005 expands application status to `submitted`, `under_review`, `in_progress`, `resolved` or `rejected`; creates immutable `complaint_status_events`; backfills a `created` event for each existing complaint at its original `created_at`; and adds indexes for admin listing/history. Workflow status remains operational state, never an ML label.

Migration 0007 adds nullable `department_id` and `assignee_user_id` to complaints; administrator-managed `municipal_departments`; many-to-many current memberships; immutable membership events; and immutable complaint assignment events containing previous/resulting ownership, actor, reason and time. Existing rows remain null/unassigned. These operational fields and histories are excluded from citizen schemas and research datasets.

## Canonical complaint record

| Group | Field | Type or form | Purpose |
|---|---|---|---|
| Identity | `complaint_id` | UUID | Stable internal identifier |
| Application | `description` | text | Citizen-provided complaint text |
| Application | `image_ref` | nullable URI/key | Reference to submitted image |
| Application | `latitude`, `longitude` | nullable decimal | Submitted or selected location |
| Application | `location_label` | nullable string | Human-readable selected place |
| Application | `location_precision` | nullable exact/approximate/broad | Truthful selection granularity |
| Application | `location_details` | nullable string | Citizen-provided nearby guidance |
| Application | `location_source` | nullable search/device/map | How the selected point was produced |
| Application | `location_accuracy_m` | nullable decimal | Accuracy when available |
| Application | `status` | controlled value | Workflow state, not an ML label |
| Application | `created_at`, `updated_at` | UTC timestamp | Record lifecycle |
| Audit | `event_id` | UUID | Immutable lifecycle-event identity |
| Audit | `previous_status`, `new_status` | nullable/required controlled status | Transition evidence |
| Audit | `event_type` | created/status_changed | Event meaning |
| Audit | `operator_note` | nullable string, max 1,000 | Internal operational context; never citizen-visible by default |
| Audit | `actor_id` | nullable UUID | Future authenticated actor; currently null |
| Audit | `occurred_at` | UTC timestamp | Immutable event time |
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

The working categories are proposed for the first feasibility pass as `civicai-category-v1` in `research/taxonomy/category_v1.json`: `road_damage`, `garbage_waste`, `streetlight`, `waterlogging`, `broken_footpath`, `drainage_sewerage`, `water_leakage` and `other`. Its status is `proposed_pending_human_approval`. `research/ANNOTATION_GUIDELINES_V1.md` defines positive/negative boundaries, multi-issue handling, the restricted meaning of `other`, modality conflicts, exclusions and adjudication. A definition change creates a new taxonomy version and may require explicit relabeling; version 1 labels are never silently reinterpreted.

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

Production runtime data is separate from research data. Runtime backups contain the PostgreSQL application database and private evidence volume only; the Docker build excludes `data/`, `research/`, `ml/`, `models/`, backups and secrets. A private tracking token is derived with HMAC from `complaint_id` and a production secret; it is not a database field, research label or log field. Its status response exposes only UUID, description, status and timestamps. Exact location/evidence/ownership remain municipal-only after submission.

The operational default is no automatic deletion. Project backup-retention examples are not legal policy. Complaint, evidence, audit-log and backup retention require an authorized real-deployment decision; no Indian municipal retention rule is claimed here. The read-only media audit detects missing, orphan and invalid evidence references without deleting files.

## Municipal identity data

Migration `0006` adds minimal operational identity data, not citizen identity. `municipal_users` stores UUID, normalized unique username, Argon2id hash, controlled role, active state and timestamps. `municipal_sessions` stores a UUID, user foreign key, SHA-256 token digest, session-bound CSRF secret, absolute expiry and revocation timestamps; raw authentication tokens are never stored. `security_audit_events` records only event type, actor/subject UUIDs and time. Passwords, raw session tokens and CSRF values are never returned in account schemas or audit events.

`complaint_status_events.actor_id` is now a nullable foreign key to municipal users. Historical Issue #8 nulls remain truthful; new authenticated status changes record the actor UUID. Citizen complaint schemas do not expose history or operator notes.

Issue #5 uses a strict JSONL manifest. Each record stores identity and source terms/basis, dataset and taxonomy versions, annotation state/label/provenance, a leakage group, split, and text/image availability plus safe relative references and SHA-256 hashes. `unassigned` is allowed during curation; only `annotated` records may enter train, validation or test. Excluded records require a reason and never receive a category. The validator can check only internal consistency and exact hashes; near-duplicate detection and source approval remain separate gates.

## Unresolved data decisions

Issue #6 preparation verifies referenced contents and builds transitive event/hash/normalized-text/decoded-pixel components. The acquired OpenCity snapshot remains a raw text curation source: 16,071 pending/unassigned records, no images and no gold CivicAI labels. Proposed mappings preserve source labels and expose decision state; their counts are not annotation results. Split proposals record independent component support as well as sample counts; those are distinct. Assignment is deterministic with 70/15/15 target probabilities and no stratification guarantee. Output remains unapproved until source, privacy, annotation, near-duplicate and class-support review. See `ISSUE_006_DATA_PREPARATION.md`.

Issue #7 Stage A review records keep reviewer pseudonym, timezone timestamp, taxonomy/mapping version, decision, rationale and decision-specific outcomes separate from immutable source context. Conflicting independent decisions require adjudication. Generated previews and reviewer files stay outside Git. A later curated manifest must preserve the original record/source identity, original source category/subcategory through its review artifact, human label basis, redaction state and approved duplicate/event group.

- Which sources are available and licensed for this taxonomy?
- Will each record have aligned text and image, or will modalities be partially missing?
- What is the unit of grouping for leakage-safe splits?
- Who may annotate, and how will disagreements be resolved?
- What severity and priority definitions can be defended?
- What minimum class support is feasible without fabricating or over-augmenting data?
