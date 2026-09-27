# Category annotation guidelines v1

Taxonomy version: `civicai-category-v1`.

## Purpose and unit

Assign one human reference category to one civic incident record for the controlled classification study. A record may contain text, an image or both. Category answers what the issue is; it does not encode severity, response priority, department or workflow status.

The annotation unit is the reported incident, not each sentence, object or photograph. Records believed to describe the same real incident must share a `group_id` even when their wording or images differ.

## Before labeling

1. Confirm the record is an urban civic issue within the project's scope and is not an emergency.
2. Review all available modalities. Do not infer details hidden by poor image quality or absent from the text.
3. Use the definitions and boundaries in `taxonomy/category_v1.json`.
4. Do not use location, identity, writing style, source website or expected department as a shortcut for category.

Emergency, criminal, medical, fire or immediate life-safety reports are excluded from this research dataset rather than labeled `other`. Records containing personal identifiers, faces, private addresses or other unnecessary personal data must be quarantined for redaction/review, not silently copied into a dataset.

## Decision rules

- Choose the issue that is explicitly presented as the primary requested municipal action.
- If a record contains several issues but one is causal context, label the requested action. Example: “Pothole filled with rainwater; repair the pothole” is `road_damage`.
- If two independent issues are equally primary, mark `needs_adjudication`; do not choose whichever class is rarer or more convenient.
- Use `other` only for a clearly eligible civic issue outside the seven named categories. Unclear, irrelevant or emergency content is excluded, not `other`.
- When text and image conflict, mark `needs_adjudication` and explain the conflict. Do not assume one modality is always more reliable.
- When the image is unusable but the text is sufficient, label from text and note image quality. The symmetric rule applies to a usable image with empty/vague text.
- A category label never implies severity or priority. A dangerous-looking example retains the same category label and awaits a separate human priority process.

## Boundary rules

- `road_damage` versus `broken_footpath`: use the surface intended for vehicles versus pedestrians.
- `waterlogging` versus `drainage_sewerage`: use `drainage_sewerage` when a drain, sewer, manhole, blockage or sewage overflow is the explicit defect; otherwise accumulated public-space water is `waterlogging`.
- `water_leakage` versus `drainage_sewerage`: clean/supply water infrastructure is `water_leakage`; waste/storm drainage infrastructure is `drainage_sewerage`.
- `garbage_waste` versus `drainage_sewerage`: waste dumped in public space is `garbage_waste`; a blocked/overflowing drain is `drainage_sewerage`, even if litter contributed.

## Annotation states

- `pending`: not yet labeled.
- `annotated`: one label has been assigned under this version.
- `needs_adjudication`: evidence is ambiguous, conflicting or multi-issue.
- `excluded`: outside scope, unusable, unsafe to retain, unlicensed, duplicate excluded by policy, or otherwise ineligible. Record the reason.

Assigned train/validation/test splits require `annotated`. Pending, disputed and excluded records stay `unassigned`.

## Review and adjudication

For a meaningful subset, two annotators should work independently before seeing each other's label. Disagreements are resolved by a documented reviewer using the same taxonomy, with the final reason retained. Agreement statistics and sample sizes may be reported only after they are actually computed.

Changes to a definition create a new taxonomy version. Do not rewrite old labels in place; preserve the original manifest and document any migration or relabeling.
