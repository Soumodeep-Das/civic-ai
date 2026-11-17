# Targeted dataset audit — 2026-11-17

Status: completed bounded discovery/fit audit; **not an exhaustive census, accepted dataset release or training approval**. Read with [ML decision specification](../docs/ML_DECISION_SPEC.md) and [coverage inventory](INDIAN_CIVIC_COVERAGE.md). Scope: Indian civic classification, image evidence/severity, contextual priority and West Bengal representation. No paid access, author outreach, restricted-data access or production-data export was performed.

## Method and stopping point

Searched the public web using the queries below, inspected promising primary publisher/repository pages and followed data-availability statements. Screened task fit, observed vs synthetic origin, geographic evidence, access, rights, label meaning and pairing. Search snippets alone did not approve sources. Earlier source inventory entries were carried forward with their original limitations, not falsely described as freshly downloaded or fully re-audited.

Exact discovery queries used on this date:

1. `Kolkata West Bengal civic complaint dataset download research images severity`
2. `India civic complaints dataset text images priority severity dataset`
3. `India drainage sewer water leakage image dataset license`
4. `India public toilet cleanliness image dataset download`
5. `"mumbai-nagar-seva-bmc" synthetic`
6. `"Kolkata" "dataset" "complaints" site:data.opencity.in`
7. `India streetlight sanitation fallen trees garbage dataset site:zenodo.org`
8. `India water leakage drainage public toilet image dataset site:data.mendeley.com`
9. `India construction debris public park damage stray animal electrical hazard image dataset license`
10. `Kolkata West Bengal waterlogging garbage dataset images Jadavpur`
11. `site:huggingface.co/datasets India civic complaints drainage water`
12. `site:data.opencity.in complaint grievance Chennai Pune Mumbai Kolkata dataset`

The pass ends with each shortlisted candidate assigned a disposition below. It does not prove every dataset was discovered. Resume targeted discovery when a label/city/language gap remains or an actionable source becomes accessible. Do not postpone all curation indefinitely while waiting for proof of global search completeness. No new real-incident training dataset was acquired during this audit; two public metadata/card snapshots were retained locally.

## Additional candidates and decisions

| Source | Primary evidence checked | Fit/access decision and follow-up |
|---|---|---|
| [CivicDex](https://huggingface.co/datasets/JadeSamLee/civicdex/blob/main/README.md) | Direct raw README read successfully; MIT stated, Tamil/Tanglish/English seed requests, category/urgency fields. Limitations and ethics sections explicitly state synthetic/realistic samples and no real citizen data | Exclude from observed-incident training/evaluation. Possible separately labeled synthetic assistant fixtures only; does not close the priority or Bengali evidence gap |
| [India_CIVICS](https://huggingface.co/datasets/Anonymous611User/India_CIVICS-Dataset/tree/main) | Search surfaced repository; direct README request returned HTTP 401 | Unresolved access/metadata; no inference about size, authenticity, Indian provenance or license; not acquired |
| [Urban_problems](https://universe.roboflow.com/akshit-bcfq2/urban_problems-c9xv0) | Page shows 47,887 images, ten categories including wires/poles, dead animals, fallen trees and vandalism; CC BY 4.0 displayed; no description and zero dataset versions | High-priority provenance/export lead, **not** verified Indian collection or usable release. Need original sources, actual export, annotation audit and related-image groups; count is publisher-displayed, not local possession |
| [Mumbai Nagar Seva competition](https://www.kaggle.com/competitions/mumbai-nagar-seva-bmc-civic-complaint-resolution-2018-2024/data) | Search describes a 1.2M-complaint competition with severity/context fields; opened page yielded no readable dataset documentation | Unresolved, not accepted as municipal observations. Original collection, real/synthetic status, rights, target construction and file access remain unverified. A search for 'synthetic' did not establish either authenticity or fabrication |
| [Zero-shot civic grievance framework](https://pmc.ncbi.nlm.nih.gov/articles/PMC12816693/) | Paper describes text/speech processing and sentiment-derived urgency; data-availability section says private artifacts available upon request for qualified non-commercial researchers | Methodology reference/request-only candidate. Not a public paired text/photo severity dataset. Do not adopt sentiment as danger, copy paper metrics, or imply author data access. No request was sent |
| [CPGRAMS API access guide](https://event.data.gov.in/wp-content/uploads/2019/12/CPGRAMS_accessing_API_HelpGuide_User.pdf) | Official search result describes grievance-detail API as restricted; document fetch timed out | Access lead only, not an acquired licensed corpus. Kaggle copies claiming CPGRAMS origin require their own provenance/privacy/rights check; no access bypass |
| [Amphan inundation, Zenodo 4390084](https://zenodo.org/records/4390084) | Publisher page and API metadata: CC BY 4.0, historical May 2020 Sentinel-derived inundation; separate WB/Odisha/Bangladesh raster files | Useful **future context** candidate. WB includes Kolkata/Haora/North and South 24 Parganas. Not live flooding, street-level depth, current traffic or complaint severity truth. India-only subset required. Metadata retained; raster files not downloaded |
| [Drains, Sanitation and Health, Uttarakhand v3](https://data.mendeley.com/datasets/2c3kzy4v93/3) | Publisher comparison describes CC BY 4.0 household survey of 1,530 households, 2004–2005 | Background/context research; not complaint photos or contemporary urban severity labels. Do not import health/household records merely because sanitation appears in the title |
| [Indian street-tree communities](https://zenodo.org/records/10655222) | Publisher describes 2019–2020 transect/tree/interview data from Kochi and Panjim | Ecology/context reference; no verified fallen-tree complaint labels. Not acquired |

Public card/metadata evidence is retained in ignored `data/external/source-audit-20261117-v1` with source URLs, check date and SHA-256. Initial direct networking failed DNS resolution; after network permission, CivicDex README and Zenodo metadata requests succeeded. India_CIVICS still returned 401. The downloadable snapshot of a README or catalog is not possession of the described incident dataset.

## Existing sources: possession and readiness

| Candidate | Possession rechecked locally | Task readiness / specific next action |
|---|---|---|
| OpenCity/IChangeMyCity Bengaluru | Complete 16,071-text snapshot; raw CSV checksum matched | Strongest candidate for a first **text-curation** release. Source labels/mappings, license details, privacy, duplicate groups and independent reference labels unresolved; no model training approval |
| DWSD West Bengal | Complete 784-image/784-mask archive; publisher SHA-256 matched | Auxiliary waste material/evidence candidate. Resolve contradictory original-image counts, augmented parents and conversion from material labels to civic-issue targets before an experiment; no urgency truth |
| Commons two pools | All 62 file hashes matched; null category/severity and unassigned split confirmed | Small relevance/negative-example review pool, not adequate multi-category model support. Verify image-level location, privacy, relevance and near duplicates before any manifest admission |
| Pune footpath | Completed metadata files matched hashes; original large archive remains `INCOMPLETE` | Resolve full acquisition and corridor/scene groups if footpath severity is selected; publisher low/medium/high labels cannot be generalized to other civic domains |
| Chennai streetlights | Earlier repository/paper lead; no image acquisition in this audit | Potential useful non-road visual source; clear dataset reuse rights still needed |
| QR4Change / Civic Issue Graph | Earlier mixed-source candidates, not newly acquired | Recover per-image Indian provenance/rights and actual pairing before use; no blanket Indian-source assumption |
| FloodDET / Roboflow Civic Grievance | Earlier candidates with unresolved image geography | Institution/author name and category labels do not establish Indian incident origin |
| RDD2022 India | Existing unacquired road auxiliary candidate | Lower acquisition priority than unresolved non-road gaps; if used, keep only verified India subset and source-scene groups |

The prior inventory provides exact links, licensing caveats and stored paths. None of the above is presently training-approved.

## Coverage verdict against the specification

| Required capability | Current evidence | Verdict |
|---|---|---|
| Broad text complaint classification | Bengaluru corpus spans waste, lighting, drainage, water supply, animals, pollution, sanitation, trees, parks and mobility | Curation feasible; evaluated label/language/city support still unestablished |
| Broad image issue classification | Waste archive; 62 candidates across 13 retrieval topics; other sources unresolved | Insufficient reviewed independent examples for a general civic classifier |
| Category-specific visible severity | Footpath label metadata; other photos lack compatible severity judgments | Not ready; category rubrics and linked evidence required |
| Contextual municipal priority | No acquired joint incident/context/independent-priority corpus | No defensible supervised priority training target; design/evaluate transparent prototype policy separately |
| Paired text/photo comparison | No approved aligned Indian incident collection | Original multimodal experiment remains conditional; unperformed is preferable to false pairings |
| WB/Kolkata generalization | West Bengal waste, source-described Commons photos; historical inundation metadata | Some local representation, no broad local evaluation benchmark |
| Bengali/Hindi/code-mixed assistance | No reviewed representative language-specific benchmark in acquired data | Cannot claim support quality; preserve explicit language limitations and review |

Unfilled photo-label gaps remain for drains/leaks, sanitation, trees, public assets, animals, electrical hazards, pollution, debris and flooding. A normal object photo is not a positive defect label. The issue domain may be covered by text without having a supported visual detector. Current application reporting remains broad regardless of model coverage.

## Ranked next work

1. Complete a reproducible OpenCity curation proposal: source-to-taxonomy decisions, privacy redaction proposal and event/duplicate groups, keeping actual reviewers and AI proposals distinct. Publish a support/readiness report before training.
2. Investigate the large multi-category Urban_problems lead and mixed-source Indian subsets; require an auditable source/export rather than relying on displayed counts. Resolve Chennai reuse rights if public documentation becomes available; author outreach is a separate explicitly authorized action.
3. Audit DWSD augmentation families and whether original scenes are recoverable. Keep it auxiliary if reliable independent evaluation is impossible.
4. Select a category-specific severity rubric only when suitable paired evidence/labels can be obtained. Do not acquire large archives solely to increase the file count.
5. Keep historical WB inundation as a future contextual candidate. Do not add GIS processing or online hazard claims to this milestone.

Exit from discovery into experiments requires a versioned release with resolved source, label and split gates, actual independent class support and a predeclared evaluation protocol. This audit satisfies the decision/discovery checkpoint, not those later gates.

## Verification

- Five completed local acquisitions retained their markers and `training_approved=false`; partial footpath archive remains excluded.
- DWSD, both Commons pools and footpath metadata files matched their stored hashes. Commons candidate labels remain null and splits unassigned.
- OpenCity raw SHA-256: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- Existing research regression: **83 passed in 9.61s** with `.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-ml-spec-20261117`.
- This checkpoint changes documentation only. No application/data-schema code, dependency, taxonomy JSON, annotation, split or model changed. No API provider was configured or paid call made. Backend/frontend/build gates were not rerun for this documentation-only change.
