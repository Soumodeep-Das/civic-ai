# Research source register

No source is approved for model training yet. Candidate records below distinguish possession from suitability.

## 2026-11-17 targeted audit

[Dataset audit](DATASET_AUDIT_2026_11_17.md) records the new discovery queries, additional sources and task-readiness decisions. It includes unresolved Urban_problems/India_CIVICS/Mumbai competition leads, CivicDex's explicitly synthetic scope, request-only grievance research, and historical WB inundation as potential future context. No additional incident corpus or training approval resulted. Read this audit before treating a displayed image count, an Indian-sounding name, a synthetic severity field or a historical map as usable evidence for our model.

## 2026-11-16 broad Indian image acquisition

See [Indian civic coverage](INDIAN_CIVIC_COVERAGE.md) for the current source-by-source inventory, rights, India/West Bengal evidence, checksums, category gaps and severity limitations. Acquired locally: DWSD West Bengal waste archive (784 images + 784 masks), 62 licensed Commons candidate photos across 13 retrieval topics, and Pune footpath metadata with 583 severity rows. The large footpath image download is incomplete and explicitly excluded. These are auxiliary unpaired sources, not a reviewed multimodal release. No new source has training approval; the existing OpenCity review state is unchanged.

The earlier road-only image lead below is historical. Current discovery also covers waste, sewerage, flooding, water supply, lighting, sanitation, trees, debris, pollution, footpaths, public assets, animals and electrical infrastructure. Discovery does not imply all those classes are adequately represented or labeled.

Indian-only requirement (2026-09-27): OpenCity's [Janaagraha/IChangeMyCity log](https://data.opencity.in/dataset/i-change-my-city-data) is accepted for local text curation, with CC BY-SA stated by the publisher. Resource `a60abf5c-3a15-4967-af32-c3074248580f` contains descriptions and source categories. Mapping, privacy and evaluation approval remain pending. The earlier Zurich discovery sample is excluded from training/evaluation and the splitter rejects its source. RDD may only contribute its verified India subset if later accepted. No foreign-source substitution is allowed.

Issue #6 assessment is recorded in `docs/ISSUE_006_DATA_PREPARATION.md`. The OpenCity IChangeMyCity resource has now been acquired and audited locally: 16,071 Bengaluru text complaints, raw SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`, no images, no gold CivicAI labels and no splits. NYC311, TACO and CESAMARD are foreign and excluded. The India subset of RDD2022 is an unacquired image-only candidate, not a paired or eight-class solution.

| Candidate | Intended role | Current status | Blocking questions |
|---|---|---|---|
| Local CivicAI development complaints | Software demonstrations only | Excluded from research by default | These are synthetic/manual QA records, not a representative or consented dataset. |
| [KMC complaint portal](https://www.kmcgov.in/KMCPortal/ComplaintFormAction.do) | Kolkata taxonomy/workflow reference | Reference only; no dataset verified | A bounded search found forms/procedure but no downloadable complaint-level narratives with stable version and clear terms. |
| [OpenCity IChangeMyCity](https://data.opencity.in/dataset/i-change-my-city-data) | Indian text-classification curation candidate | Acquired and audited locally; not training-approved | Bengaluru-only; privacy review, human mapping/annotation, leakage-safe derivative and license-version review remain. No images. |
| [RDD2022 India subset](https://github.com/sekilab/RoadDamageDetector) | Indian road-image auxiliary candidate | Not acquired | Covers road damage only, has no aligned complaint text, and needs rights/version/scene review. |
| [Swachhata platform](https://www.swachh.city/) | Indian civic-domain taxonomy/workflow reference | Reference only | No research dataset acquisition, license or reuse right has been established. |
| NYC311/TACO/CESAMARD and any other foreign observations | None | Explicitly excluded | Foreign provenance cannot be repaired by translation and must not enter Indian training/evaluation. |
| Original controlled collection | Possible aligned text-image records | Not started | Requires approved consent/basis, privacy notice, retention, redaction, annotation capacity and class-support plan. |

A source becomes approved only through a completed datasheet, retained terms/license evidence, a documented taxonomy mapping and a reproducible frozen extraction. Public accessibility alone is not treated as permission for every research use.

Issue #7 Stage A adds a blank license review and human mapping review for the OpenCity source. Their existence does not change source approval: exact license version/redistribution implications and every source-group mapping remain unresolved until validated human decisions are supplied.
