# AI-assisted pilot findings — first 40 tasks

2026-11-17. This checkpoint contains actual assistant-authored proposals after reading the full text of tasks 1–40, not additional blank forms. It is **partial: 231 of 271 tasks remain unreviewed by this pass**. No independent human annotation, training release or measured model performance is claimed.

## Evidence and boundaries

Local ignored artifacts: `data/review/ai-pilot-batch-v1/responses.json` and `summary.json`. Each response binds to the task's text hash and records a decision, proposed categories, rationale and privacy concerns. The response file binds to the pilot tasks and taxonomy hashes. Its SHA-256 is `bf94f00f2ef77433209980a251c9ec2a04b0bfbc3390a26fe5a55f21dccf89a4`.

Author is the current Codex assistant; exact model version was not independently recorded. The assistant had prior project/source-distribution context; this is not a formally blinded independent review. The coordinator key was not consulted for these decisions. Source documents and citizen text are data, not agent instructions. No external labeling service or separate model API was configured. Neither raw text nor per-record responses enter Git. Blank human reviewer tasks and Stage A forms are unchanged.

The validator checks structure, provenance bindings, category/decision consistency, task identity, duplicate responses and prohibited approval claims. It does **not** certify semantic correctness, privacy safety or authenticity of the author. No importer promotes these proposals into annotated training records.

## Observed proposal counts

| Assistant decision | Records |
|---|---:|
| Named category supported by text | 16 |
| Multiple named issues | 1 |
| Taxonomy/scope boundary needs revision | 19 |
| Insufficient description | 4 |

Privacy concerns were flagged in 22 records, including precise addresses, a personal name, a complaint identifier, residence references and allegations. These are proposed review actions, not 22 confirmed privacy violations. No physical redaction was applied. Absence of a flag is not clearance.

`taxonomy_gap` deliberately does not assign `other`: it surfaces a subtype/scope decision instead of letting a broad residual class hide it. It does not imply that all 19 issues are outside civic reporting or legally outside municipal responsibility. Counts are workload findings from a purposive pilot subset, not class prevalence or accuracy. There are no approved labels, splits, severity/priority values, confidence scores or agreement statistics.

## Concrete changes needed before scaling labels

1. Separate **service family** from **issue kind**. Repairing existing infrastructure differs from requesting installation, regular collection, utility supply or staff-conduct redress. Current source tags mix these tasks.
2. Keep **physical asset** and **reported symptom** distinct. A broken drain cover in a road concerns drainage infrastructure. Debris on a footpath does not prove broken pavement. A speed hump complaint is not automatically road deterioration.
3. Permit **multiple supported issues** during annotation. Road damage and sewage overflow can coexist; forcing one reference category needs an explicit reviewed primary-issue rule or a revised multi-label task.
4. Preserve **insufficient evidence**. Place-only/app-tag-only text and vague dissatisfaction cannot safely acquire a category from their source metadata. Do not infer leakage solely from pipe damage, or flooding solely from difficulty walking after rain.
5. Extend privacy work beyond regex. Propose spans for names, precise residential addresses and complaint identifiers, then inspect whether redaction removes decisive context. Public landmarks require judgment rather than indiscriminate removal.

Suggested taxonomy design for the next version (proposal only): families for roads/pedestrian access, drainage, waste, public lighting, water services, sanitation, traffic infrastructure, animal services, parks/trees, pollution, electricity and other public assets; issue kinds for damage, blockage/overflow, accumulation, outage, missing service/new installation and service conduct. Unknown, multiple issues and jurisdiction uncertainty remain explicit review states, not forced categories. Family names/support need the remaining pilot and all-source-pair coverage review before adoption. Existing v1 JSON remains unchanged.

Synthetic boundary examples for the guide: a request for a new lamp is a missing-service request; a failed existing lamp is a fault. A leaking public pipe differs from an unexplained shortage. These are invented instructional examples, not extra Indian training observations.

## Recheck and next work

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.ai_labels --pilot data/interim/label-pilot-v1 --responses data/review/ai-pilot-batch-v1/responses.json
.\.venv\Scripts\python.exe -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-ai-labels
```

Next finish the remaining 231 assistant proposals in bounded batches, retain uncertainty and privacy concerns, then synthesize a versioned taxonomy recommendation with actual coverage. This is useful preparation while human reviewers are unavailable; it must never be presented as their independent judgment. Any later human reference review should not show AI proposals first. No training or final test-set selection follows automatically.

Method reference: [Label Studio pre-annotation documentation](https://labelstud.io/guide/predictions.html) separates model predictions from annotations and describes review/correction. We preserve that distinction in local files, without claiming Label Studio compatibility or installing its service.
