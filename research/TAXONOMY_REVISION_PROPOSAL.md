# CivicAI taxonomy revision proposal

Version: `civicai-taxonomy-revision-draft-1`, 2026-11-17. **Design proposal, not adopted taxonomy or training approval.** Based on the full 271-task AI pilot and the earlier source inventory. The active `category_v1.json`, source mapping rules, APIs and application remain unchanged. No cross-city or Bengali generalization is established.

## Recommendation

Describe an issue with a **service family**, **asset/subtype** and **observed issue kind**, keeping public/private setting and uncertainty explicit. Retain multiple issue descriptions when the text supports them. Do not immediately train a large classifier for every combination: only experimentally supported targets should become model outputs after review.

The pilot supports the need for this separation, not final class definitions. Its 86 gap cases include service requests, private-property boundaries and mixed requests; they are not 86 examples of one learnable `other` class. Its 14 multi-category proposals are not a prevalence estimate. Additional mixed cases currently sit in the gap bucket because v1 cannot express all their components.

## Proposed service families and scope

| Family proposal | Distinctions to preserve | Evidence boundary |
|---|---|---|
| roads_and_pedestrian_access | carriageway vs footpath; deterioration vs new paving; obstruction vs structural damage | Many pilot descriptions; not independently labeled |
| drainage_and_sewerage | drain/sewer/manhole; blockage, missing cover, overflow, odor, grading | Odor alone does not prove blockage; sewage accumulation is not clean-water leakage |
| solid_waste | public dumping/accumulation; collection failure; bins; construction residue | Household waste collection failures differ from public dumping |
| public_lighting | existing fault; switch/timer fault; restoration of removed equipment; new installation | Traffic signals and private electricity are excluded from this family |
| water_services | supply leakage; damaged pipe without stated leakage; shortage; meter/connection; extraction concerns | Fluid source/ownership can remain unknown; do not infer clean supply from an unspecified leak |
| sanitation_and_public_health | public toilets, urination, carcass removal, vector control | Symptoms do not establish disease causation or a severity label |
| mobility_and_traffic_infrastructure | traffic signals, speed humps, parking/obstruction, bus-stop access | Design problems differ from asset deterioration; jurisdiction requires review |
| animals | animal services and public-space concerns | Vaccination status/aggression may be unverified claims; not all requests establish danger |
| parks_trees_and_waterbodies | vegetation/parks/lake conditions and access | Broader source inventory; pilot support does not establish sufficient training coverage |
| pollution_and_nuisance | waste burning, air/noise concerns, odor | Distinguish source, observation and inferred harm; broad coverage remains incomplete |
| electricity_services | utility supply/cable issues | Private connections require scope review; no automatic municipal routing |
| public_assets_and_space | signage, abandoned objects, public-space encroachment | Avoid converting ownership/legal allegations into established facts |

`service_conduct` should be a cross-cutting issue kind with a family when known, not a physical-defect category. Residual `other_eligible` is permitted only after eligibility and exclusion review; it must not hide unreadable text, missing context or unsupported families. Families can still be merged/split after coverage review; these names are not yet a machine-readable label release.

## Proposed annotation contract

For each described issue, record family, asset, issue kind (`damage`, `blockage`, `overflow`, `leakage`, `accumulation`, `outage`, `obstruction`, `missing_service`, `new_installation`, `maintenance`, `design`, `service_conduct`, or `unknown`), evidence basis and uncertainty. These kinds are a draft list, not freely combinable approved targets. Record `public`, `private`, `mixed`, or `unknown` setting without guessing ownership from an address. Record whether the complaint describes a present defect, recurring condition, future request, resolved event or unclear time state.

Use explicit record-level outcomes: sufficient evidence; clarification needed; corrupted/unusable language; multiple issues; scope/jurisdiction review. Keep language, privacy status and duplicate/event adjudication separate. Record factual observations separately from allegations, feared outcomes and claimed durations/affected populations. Severity and operational priority remain separate tasks; urgency words, source tags and model confidence do not supply their ground truth.

## Preserve v1 compatibility while collecting richer evidence

| v1 target | Candidate mapping under the draft, subject to reference review |
|---|---|
| road_damage | roads family + carriageway damage/restoration; exclude new unpaved-road provision unless reviewed definition changes |
| broken_footpath | roads family + pedestrian-surface damage/restoration; not parking or absence of a never-built pavement |
| drainage_sewerage | drainage family + explicit defect/blockage/opening/overflow; cover also used as pavement may need dual asset roles |
| waterlogging | explicit public accumulated rainwater; retain cause unknown unless separately evidenced |
| garbage_waste | solid-waste public accumulation/dumping; collection service alone is insufficient under current definition |
| streetlight | public-lighting existing equipment fault/restoration, not new installation or traffic signal |
| water_leakage | public supply-water escape; unknown/private/sewage sources remain unresolved |
| other | no bulk remapping; independently establish eligibility and support |

For the first eventual baseline, retain a reviewed single-label subset or explicitly revise the study to multilabel; do not silently discard mixed cases or force a dominant category. Report how many records are excluded/deferred and how that affects applicability. The [scikit-learn target guide](https://scikit-learn.org/stable/modules/multiclass.html) distinguishes multiclass and multilabel problem definitions; changing them changes evaluation. This is a methodological distinction, not a recommendation to install a new estimator now.

## Decisions still needed before adoption

Follow-up: [CURATION_QA_REPORT.md](CURATION_QA_REPORT.md) now supplies the full 231-pair coverage proposal and bounded duplicate/privacy QA evidence. This completes the inventory step below, not the remaining record-level/scope adjudication or adoption gates.

1. Audit all 231 source category/subcategory pairs against these families and document unmapped/mixed cases. Source labels are hints, not record reference truth.
2. Revisit tentative pilot labels and consistency boundaries. Some provisional water-leak labels include a public-location clue but no confirmed supply source; this is a review requirement, not sufficient training evidence.
3. Review near-duplicate candidates before splitting. The pilot's distinct template groups do not establish scene independence. Preserve original records and propose links, not automatic deletion.
4. Propose and validate privacy redaction spans without removing issue evidence. Keep personal names, residential addresses, contact/complaint identifiers and allegations out of published artifacts.
5. Obtain independent reference review/adjudication; document any unavailable review. AI-assisted exploratory labels cannot be called human gold or used to manufacture validation results. [Label Studio's prediction guidance](https://labelstud.io/guide/predictions.html) likewise treats pre-annotations as predictions for review/correction.
6. Only then freeze a versioned taxonomy/mapping and compatible manifest migration, rights decision, support table and split protocol. No automatic migration of production complaints or old experiments.

This draft advances label design without changing the tested application or claiming all-India civic coverage. Image task definitions, visible severity rubrics, paired-data requirements and contextual priority remain separate workstreams.
