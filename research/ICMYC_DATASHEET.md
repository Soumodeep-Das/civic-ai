# IChangeMyCity Indian text curation snapshot

Status: acquired and audit-complete for curation; not approved for training or final evaluation.

## Provenance and rights

Publisher: OpenCity, organization/attribution: Janaagraha iCMyC, dataset author: Vaidyanathan R. Source type: Indian civic-tech/open-data publisher. [Catalogue](https://data.opencity.in/dataset/i-change-my-city-data), [machine-readable metadata](https://data.opencity.in/api/3/action/package_show?id=i-change-my-city-data). Catalogue metadata was created 2023-04-15 and modified 2025-11-27; resource metadata was created/last modified 2025-11-25. Resource `a60abf5c-3a15-4967-af32-c3074248580f` is titled “I Change My City Complaints Log - 2019 - 2022”. Its direct CSV URL is `https://data.opencity.in/dataset/9183b0b2-b49a-40a9-b36d-275e1eaedb3f/resource/a60abf5c-3a15-4967-af32-c3074248580f/download/5f99b09a-64b5-45f0-ab18-4cf0a0cabf6d.csv` and publisher-reported size is 8,377,752 bytes.

The catalogue declares Creative Commons Attribution Share-Alike (`cc-by-sa`). Required attribution is therefore recorded as OpenCity/Janaagraha iCMyC and dataset author Vaidyanathan R. The exact Creative Commons version and derivative redistribution details are **UNKNOWN / UNVERIFIED** because the retained metadata does not identify a version-specific license URL; verify them before distributing any derivative. Local acquisition does not establish consent for unrelated uses.

Scope: Bengaluru Indian civic complaints. This log is a new distribution lead despite the previously discovered deprecated AWS distribution; do not conflate the two. No inference of all-India representativeness is made.

Format: CSV. Fields: `created_at`, `ward_id`, `title`, `description`, `sub_category_id`, `civic_agency_id`, `location`, `address`, `latitude`, `longitude`, `ward_title`, `category_id`, `category_title`, `sub_category_title`, `civic_agency_title`, `complaint_status_title`, `comment_count`. Modality: complaint text and structured metadata only; no verified image field. Verified record-year coverage is 2019–2022.

## Storage and transformations

`data/raw/icmyc-india-v2` is the completed ignored local snapshot. It contains 16,071 records and is pinned by raw SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. Retain publisher metadata, original CSV, an acquisition report, source-category metadata and UTF-8 description files. The source has no stable complaint ID column, so IDs use the raw snapshot hash and CSV record number (not physical line number, since descriptions can contain newlines). New exports require cross-version duplicate checks.

UTF-8 is attempted first; the observed CSV requires Windows-1252 for punctuation. Decoding is strict: no replacement characters are introduced by the importer. Whitespace is trimmed at description boundaries. Source category, subcategory, location, agency, resolution and status are not prepended to descriptions. Images are absent. Labels remain pending/null and all splits remain unassigned.

The original CSV includes addresses/coordinates and free text may include personal data. Keep this snapshot local and access limited; inspect/redact a derived version before model use or sharing. No author names, addresses, complaint texts or raw samples go into Git. Counts/checksums can be documented.

## Audit summary and outstanding acceptance review

The reproducible `icmyc-audit-v5` audit found 7,843 high-confidence mapping proposals, 2,255 ambiguous, 5,955 needing review and 18 rejected missing-label records. Accepted-proposal support ranges from 3,350 garbage/waste to 56 water-leakage records. It also found 733 normalized-description excess duplicates, 618 extremely short texts and possible phone/email patterns in 196/11 records. These automated signals require human review and do not create reference labels.

- Normalize the mixed dash day-month-year and slash month-day-year source formats explicitly.
- Inspect empty/sentinel/HTML descriptions and duplicate/template text.
- Map precise source subcategories to versioned CivicAI categories; broad categories are insufficient (roads/footpaths are combined).
- Keep source-provided labels distinguishable from agent suggestions and independent human annotation. No inter-annotator agreement is claimed.
- Audit rare classes, conflicting labels, related incidents, near duplicates and source artifacts before splitting.
- Preserve the distinction between missing photos and truly aligned multimodal observations.
- Determine a retention and redaction procedure before accepting a model-ready derivative.

No model metrics, annotator agreement, final class counts or train/test assignments are available at this stage. Bengaluru-only coverage does not establish Kolkata, West Bengal or all-India performance.

## Issue #7 review state

Stage A generated `issue7-review-v5` locally with blank taxonomy, mapping, privacy, priority-record, duplicate, license and final approval forms. The package is checksum-bound to this snapshot and remains ignored. It contains no human decision, approved label, curated class count or agreement result. Any Stage B derivative must cite validated reviewer/adjudication artifacts and preserve source identity, original labels, redaction state and duplicate group.
