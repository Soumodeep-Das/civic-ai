# Indian civic data expansion

Follow-up: [2026-11-17 targeted audit](DATASET_AUDIT_2026_11_17.md) adds discovery evidence and readiness decisions against the [ML decision specification](../docs/ML_DECISION_SPEC.md). The acquisition counts below remain unchanged; broader discovery does not imply training readiness.

Acquisition/research checkpoint: 2026-11-16. This is a coverage inventory, not a trained model or a new approved taxonomy. The user explicitly requires broad Indian civic coverage, with West Bengal representation where available. Road-image availability must not determine CivicAI's entire scope.

## Data actually held locally

| Source | Acquired | Rights/provenance evidence | Current use |
|---|---|---|---|
| OpenCity/IChangeMyCity Bengaluru | Existing 16,071 text records; no images | Retained publisher metadata; existing CC BY-SA/version review remains pending | Text curation, unchanged Stage A review package |
| [DWSD v1](https://data.mendeley.com/datasets/gr99ny6b8p/1), DOI `10.17632/gr99ny6b8p.1` | 784 RGB images and 784 segmentation masks in a 252,719,363-byte archive | Publisher CC BY 4.0; [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11848783/) identifies Jadavpur/Kolkata, Garia and Berhampore, West Bengal | Waste-image auxiliary candidate; no severity or complaint-text labels |
| Wikimedia Commons civic review pool | 62 distinct photos; 42 have Kolkata/Howrah/West Bengal/Calcutta in source title or description | Per-image source URL, author, license metadata and checksums retained; country is source-described, not independently geolocated | Small discovery/review pool across 13 topics; not a balanced benchmark |
| [Indian Footpath Damage Segmentation Dataset](https://zenodo.org/records/17154852) | Metadata, license, README and 583 severity rows: low 130, medium 262, high 191 | Publisher describes Pune collection; CC BY 4.0; three small files match publisher MD5 | Severity-method reference/candidate. Image archive **not acquired** |

All new acquisitions have `training_approved=false`. Commons records have null category/severity, pending annotation/privacy review and unassigned split. Publisher labels are not silently converted into CivicAI labels. No AI-generated example or caption is counted as an observed Indian complaint.

Local snapshots, all ignored by Git:

- `data/raw/dwsd-west-bengal-v1`: complete archive, source metadata and publisher file metadata.
- `data/raw/commons-indian-civic-v1`: 42 photos, 180,481,072 image bytes.
- `data/raw/commons-indian-civic-gaps-v1`: 20 further photos, 89,834,076 image bytes.
- `data/raw/footpath-india-metadata-v1`: complete **metadata-only** acquisition.
- `data/raw/footpath-india-17154852-v1`: interrupted 4,504,525,071-byte archive request, stopped after 55,574,528 bytes stopped advancing. Retains `INCOMPLETE`, `interruption.json` and `.zip.partial`; never count or train from it. No background transfer remains running.
- `data/interim/indian-image-acquisition-audit-v1`: local archive and cross-pool audit summaries.

`COMPLETE` means the requested acquisition completed, not that training is approved. For footpath, inspect `archive_downloaded` explicitly.

## Broad coverage and outstanding gaps

Text counts below are original publisher categories, sometimes summed across spelling/category variants. They are not verified CivicAI annotations. Photo counts are retrieval topics, **not positive issue labels**: a streetlight, cow or toilet photograph may show no defect at all.

| Civic domain | Existing text evidence | Newly acquired image evidence | Gap before a defensible classifier/severity study |
|---|---|---|---|
| Waste, litter and dumping | 3,952 waste/garbage records | DWSD 784 images + 5 Commons candidates | Original-scene groups, civic-vs-material label mapping; disposal site is not automatically illegal dumping |
| Sewerage, blocked/open drains | 301 sewerage + 138 storm-drain records | 4 Commons candidates | More independent scenes and obstruction/overflow labels |
| Waterlogging/flooding | Source subcategories need curation | 5 Commons candidates | Flood depth, duration and hazard cannot be reliably inferred from arbitrary photos |
| Water supply/leakage | 341 records | 1 Commons candidate | No adequate Indian leak-vs-normal image dataset verified |
| Streetlights | 1,500 records | 3 Commons candidates; Chennai dataset located below | Daytime unlit lamp is not evidence of failure; rights/night coverage |
| Public sanitation/toilets | 61 public-toilet + 39 sanitation records; 948 separate Yellow Spot records | 4 Commons candidates | Condition labels, private-person exposure and nonvisual complaints |
| Trees/storm damage | 104 trees/saplings records | 10 Commons candidates | Distinguish healthy vegetation from obstruction/damage; group storm/event photos |
| Construction debris | Requires subcategory review | 2 Commons candidates | Separate active permitted works, debris and actual access obstruction |
| Pollution/water bodies | 437 pollution + 54 lake records | 9 Commons candidates | Photo cannot establish water chemistry, noise level or air quality |
| Footpath/accessibility | 5,072 broad mobility + 113 roads/footpaths records; not all footpaths | 3 Commons candidates; Pune severity metadata | Full image acquisition, access/damage labels and corridor grouping |
| Parks/playgrounds/public assets | 129 parks/garden/recreation/playground records; 133 community infrastructure/services records | 5 Commons candidates | Normal asset vs damage; asset-specific severity definitions |
| Animals in public spaces | 860 animal-related records | 7 Commons candidates | Animal presence is not aggression, neglect or a municipal hazard |
| Electrical/public-safety hazards | 241 electricity/power records; fire/safety source groups also exist | 4 Commons candidates | A visible wire is not proof it is live or dangerous; expert-confirmed targets absent |
| Road damage/traffic assets | Existing broad mobility groups + 967 traffic/road-safety records | RDD2022 India remains a candidate; no new road archive acquired | Keep as one supported domain, not the definition of CivicAI |
| Other civic service complaints | Remaining source groups include transport and administrative services | No general photo solution | Preserve unknown/multiple/nonvisual handling; do not force every complaint into a visual category |

The [KMC services directory](https://www.kmcgov.in/KMCPortal/jsp/KMCService.jsp) is a local scope reference, not a licensed complaint dataset. The table is a coverage target; none of these counts establishes all-India or all-category model performance. Bengali, Hindi, English and code-mixed language coverage still need measurement.

## Other sources inspected

| Primary source | Finding | Decision |
|---|---|---|
| [Chennai streetlights repository](https://github.com/Team16Project/Street-Light-Dataset), [paper](https://arxiv.org/abs/2407.01117) | Indian functional/nonfunctional streetlight collection. Repository tree inspected at `ea5d98adb6b0beefa5fcb79fbcb745073244a8e9`; no dataset LICENSE found | Hold images until reuse rights established. Paper availability does not license photographs |
| [QR4Change v2](https://data.mendeley.com/datasets/zndzygc3p3/2) | CC BY 4.0; reports 1,971 garbage and 2,966 road images; Pune field images mixed with web/repository/portal sources | Need per-image Indian subset and original rights; do not call entire collection Indian |
| [Civic Issue Graph dataset](https://github.com/Sshanu/civic_issue_dataset), [2019 paper](https://mohitjaindr.github.io/pdfs/c26-www-2019.pdf) | Multi-object civic annotations, repository MIT license; paper mixes FixMyStreet and IChangeMyCity plus other datasets | Candidate for provenance audit; repository license does not settle every third-party photo's rights. Do not import mixed-country pool |
| [FloodDET](https://data.mendeley.com/datasets/px48m7vwvf/1) | IIT Guwahati publication; underlying sources include DEEPFLOOD, FloodIMG, Mapillary and COCO | Institution location does not establish Indian photo origin; exclude unresolved records |
| [PMGSY waterlogging study](https://isprs-annals.copernicus.org/articles/X-5-W2-2025/203/2025/isprs-annals-X-5-W2-2025-203-2025.pdf) | Describes Indian citizen-app images | No verified public licensed image release acquired; do not scrape private reports |
| [DataCluster Indian garbage](https://huggingface.co/datasets/Dataclusterlabspvtltd/Domestic-Trash-Garbage-Dataset) | India-specific; limited sample/full-data licensing and redistribution restrictions | Not an unrestricted training source; no paid purchase or image acquisition |
| [Roboflow Civic Grievance](https://universe.roboflow.com/rishi-yadav/civic-grievance) | Multiple relevant visual classes | Indian origin unverified; author/name/class labels are insufficient |
| [IndiaScene365](https://data.mendeley.com/datasets/pwffhg6nhz/1), [paper](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1669512/full) | Indian traffic/scene objects, including animals and traffic lights | Context/negative-example candidate; not civic defect/severity truth, not acquired |

This was a bounded search, not proof that no other dataset exists. Foreign, unlicensed, inaccessible and mixed-origin sources are not substitutes for missing Indian observations. Paid services and account-gated downloads were not used.

## Integrity findings and severity design

DWSD archive SHA-256 is `fb9229c330ed253f4fb7c18bd46dddebe4df6f8d3f602747f505ff7601a11737`, matching the publisher. ZIP CRC checks pass. All 784 images and masks decode at 448×448. Pairing must use `Image/img_ID.png` → `Mask/mask_ID.png` in the same publisher split; 784/784 IDs match. Masks contain values 0–15; the paper treats 0 and 15 as background. No exact decoded-RGB duplicates were found, including across the publisher train/test folders. This **does not** rule out crops, rotations or shared scenes.

The DWSD paper gives inconsistent original-image descriptions: it reports 784 selected images but later describes augmentation from only 52 and release of augmented data. Its 640/144 split must not be adopted as a leakage-safe CivicAI split without reconstructing parent scenes. Report 784 image files, not 784 proven independent incidents. It supplies material masks, not urgency labels.

All 62 Commons downloads decode and match their recorded SHA-256; both pools have 62 distinct page IDs and file hashes combined. License counts: CC BY 2.0 (7), CC BY 3.0 (16), CC BY 4.0 (3), CC BY-SA 2.0 (1), CC BY-SA 3.0 (9), CC BY-SA 4.0 (24), public domain (2). Preserve per-image attribution and applicable share-alike conditions when making derivatives. Near-duplicates, source-described location, relevance, faces/plates and event grouping remain unreviewed. The pools cannot support a serious generalization claim at this size.

Severity and priority remain separate targets:

1. Identify supported issue types and visible evidence, allowing multiple issues and unknown/unusable input.
2. Estimate **visible severity only where defensible category-specific labels exist**; permit `cannot_assess`. Classification confidence is not severity.
3. Combine confirmed evidence with reported duration, affected access/services and other justified context for a transparent municipal priority proposal. Do not infer hidden electrical state, flood depth, structural safety or disease risk from appearance alone.
4. Record AI-assisted annotations explicitly as proposals/silver labels. They cannot impersonate independent human ground truth or evaluate the same model that generated them.

Before experiments: audit privacy and licenses, group original scenes/augmentations/events, retain Indian negatives and confusing cases, version taxonomy changes, establish label support, and evaluate by held-out city/source as well as class. Genuine paired text/photo incidents are required for the original modality-comparison study; pairing unrelated images with same-category text or generating captions does not satisfy it. The current eight-class proposal and Stage A review artifacts are unchanged.

## Reproduction

See `research/README.md` for exact acquisition and test commands. The collector stores source responses, rejects unexpected hosts/redirects, checks publisher hashes where supplied, caps downloads, refuses overwrites and keeps incomplete acquisitions visibly incomplete. Search results may change; retained responses and checksums identify this acquisition, while a fresh run must use a new output directory.

No application, API, deployment, model, training split or claimed result changed. OpenCity raw SHA-256 remains `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
