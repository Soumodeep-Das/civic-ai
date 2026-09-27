# Issue #6 — India-only dataset audit and preparation

Status: source acquisition and reproducible audit complete; human review, annotation, image acquisition and training approval remain incomplete. No model has been trained and no metric is claimed.

Evidence labels used here: **VERIFIED FACT** means reproduced from the retained source/artifact; **PROJECT DECISION** is an enforced CivicAI rule; **PROPOSED DECISION** needs human approval; **UNRESOLVED** is not assumed true.

## Jurisdiction rule

Training and evaluation are restricted to verified Indian civic observations. Kolkata/KMC and West Bengal sources have priority, followed by other Indian municipal sources. Foreign records, including an earlier local Zurich discovery sample, are excluded from manifests, curation, splitting, training and evaluation. Translation does not convert a foreign observation into Indian data.

## Bounded Kolkata/West Bengal discovery (2026-09-27)

The official [KMC complaint form](https://www.kmcgov.in/KMCPortal/ComplaintFormAction.do) and [complaint procedure](https://www.kmcgov.in/KMCPortal/jsp/ComplaintProcedure.jsp) confirm locally relevant issue types and a central complaint workflow. They are useful taxonomy/workflow references. Bounded searches of the KMC portal, West Bengal municipal/urban-development pages and data.gov.in did not locate a downloadable complaint-level dataset with reusable narratives, stable version and clear research-use terms. This means **no usable source was verified in this search**, not that none exists. No page was scraped and no complaint data was inferred from the forms.

## Frozen Indian source snapshot

OpenCity publishes the [IChangeMyCity complaints log](https://data.opencity.in/dataset/i-change-my-city-data), attributed to Janaagraha/iCMyC. Resource `a60abf5c-3a15-4967-af32-c3074248580f` is a Bengaluru complaint CSV titled for 2019–2022. Publisher metadata states `cc-by-sa`; exact attribution and linked-license-version requirements still need review before redistributing a derivative.

The local ignored snapshot `data/raw/icmyc-india-v2` contains the original CSV and publisher metadata, acquisition report, separate source-label file, manifest and UTF-8 text files. Its immutable identifiers are:

- dataset version: `icmyc-d951dbb48453`
- raw CSV SHA-256: `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`
- publisher metadata SHA-256: `9f79f5cc1e3786b1b26a81975d1e355fc9f74d0dc112e53e684417a47eadb31a`
- records returned/ingested: 16,071/16,071; omissions: zero
- source encoding: Windows-1252, decoded strictly and exported as UTF-8 text
- modalities: text only; zero image fields and zero paired images
- labels/splits: every manifest record remains `pending`, null category and `unassigned`

The integrity gate re-hashed the raw artifacts and every manifest-referenced text file before replacing `INCOMPLETE` with `COMPLETE`. Raw complaint content and review artifacts remain outside Git.

## Reproducible audit results

Run:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.audit data/raw/icmyc-india-v2 --output data/processed/icmyc-audit-v5
```

The ignored output records counts and content references without copying complaint text into Git. Script/language screening is deliberately described as evidence, not ground-truth language identification.

| Check | Result |
|---|---:|
| Raw/manifest records | 16,071 / 16,071 |
| Valid global coordinates / inside broad India bounding box | 16,071 / 16,071 |
| Years | 2019: 7,383; 2020: 4,492; 2021: 2,645; 2022: 1,551 |
| Latin-script English-or-transliterated bucket | 16,034 |
| Unknown/other-script bucket | 37 |
| Extremely short descriptions | 618 |
| URL-only descriptions | 1 |
| Missing address | 7,193 |
| Missing source category / subcategory / ward | 32 / 18 / 32 |
| Exact-row duplicate excess | 33 across 26 groups |
| Normalized-description duplicate excess | 733 across 303 groups |
| Simple template duplicate excess | 790 across 337 groups |
| Possible phone / email patterns | 196 / 11 |

The largest original source categories are Mobility—Roads/Footpaths/Infrastructure 5,072; Garbage/Unsanitary Practices 3,946; Traffic/Road Safety 967; Yellow Spot 948; Animal Husbandry 859; Street lighting 807; Streetlights 693; Pollution 437; Water Supply and Services 320; Sewerage Systems 301; and Storm Water Drains 138. The complete original category and subcategory distributions are retained in `audit.json`; no broad source category is silently relabeled.

Dates use 6,405 dash-separated day-month-year values and 9,666 slash-separated month-day-year values. The slash records all have a second component above 12, so their order is inferable, but the source's mixed formatting must still be normalized explicitly in any derivative.

No title, description, date or coordinate pair is missing after acquisition; all dates parse under the two observed formats. There are 198 distinct nonmissing ward values. The dataset has no stable publisher complaint-ID column; generated source identities are unique and snapshot-specific. No Bengali- or Devanagari-script text was detected; 16,034 descriptions use Latin script and may include English or transliteration, which this conservative audit cannot distinguish. The remaining 37 require script/language review. No reliable automated spam judgment is made beyond URL-only, extreme-length and repeated-template signals.

Privacy matches are screening signals with false positives and false negatives. The review queues store record IDs, local text references, fingerprints and reasons—not raw text. Audit v5 creates 65 deterministic hash-sampled mapping examples, 854 quality/privacy/language references and up to 400 highest-size duplicate/template groups. Human redaction/exclusion decisions are still required.

## Proposed mapping—not labels

`research/mappings/icmyc_v1.json` makes each exact source-subcategory decision visible as `accepted`, `ambiguous`, `needs_review` or `rejected`. Source labels are preserved separately and are never overwritten. The taxonomy file itself is marked `proposed_pending_human_approval`.

- high-confidence accepted proposals: 7,843
- ambiguous proposals: 2,255
- needs human review/unmapped: 5,955
- rejected for missing source subcategory: 18

Accepted-proposal counts are road damage 2,252; garbage/waste 3,350; streetlight 1,294; waterlogging 226; broken footpath 305; drainage/sewerage 360; water leakage 56. The largest/smallest ratio is about 59.82. No source rule currently establishes `other` as a reliable positive class. These are mapping-candidate counts, not gold labels, final class counts or training approval.

## Image and multimodal status

No usable Indian paired text-image source is possessed. The author repository for [RDD2022](https://github.com/sekilab/RoadDamageDetector) describes road-damage images/box annotations spanning several countries, including an India subset, and states CC BY-SA 4.0 for images. It neither supplies citizen complaint text nor covers the eight classes; public test labels are absent, and the India sample count, archive checksum and page-update date remain **UNKNOWN / UNVERIFIED** here because no archive was downloaded. It is therefore only an unacquired auxiliary candidate, not accepted CivicAI data. Unrelated text and images must never be paired to simulate multimodal observations. Any later image source needs independent rights, geography, privacy, scene-duplicate and label review.

## Preparation contract and remaining gates

`research.civicai_research.prepare` verifies referenced bytes and groups source events, exact/normalized text duplicates and identical decoded images transitively. It refuses foreign/unreviewed sources, existing assignments and output overwrite. Deterministic 70/15/15 component hashing is a proposal, not stratification or guaranteed class coverage. Successful output is marked complete but always reports `training_approved: false`.

Before training: human-review the proposed taxonomy/mapping; inspect and redact privacy queues; adjudicate ambiguous/multi-issue/short/template records; freeze a reviewed Indian text derivative; group duplicates/related events before splitting; document class/source/geographic/language limitations; and make an explicit training-approval decision. Paired multimodal comparison remains blocked until genuine aligned Indian images exist.

Human handoff files are `mapping-review.json`, `suspicious-review.json` and `duplicate-review.json` in the ignored audit directory. Reviewers should decide mapping rules, inspect all flagged privacy/language cases, adjudicate the largest duplicate/template groups, and record decisions in a new versioned artifact; they must not edit raw data or mark ambiguous records accepted in place.
