# Reviewed development export

2026-11-19. `research.civicai_research.release` implements a private review packet and minimal redacted development export. It does not approve training, create a test set or change the baseline runner's real-data refusal.

## Current result

Prepared all 271 pilot reports in ignored `data/review/development-release-review-v1`. Every decision starts pending and every gate starts false. Attempting export with this actual pending ledger exited 1 without producing an export directory. No real record has been released, physically redacted in the source, or used for model fitting.

## Workflow

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.release prepare --pilot data/interim/label-pilot-v1 --readiness data/review/baseline-readiness-v2 --context data/review/context-review-validated-v1 --output data/review/development-release-review-v2
```

Use a fresh directory. `packet.json` is immutable and hash-indexed. It retains original pilot text, proposed labels, privacy flags, proposed redaction spans and conservative containment groups, including excluded/unclear reports. Treat the entire packet as private personal-data-bearing material. `decisions.json` is deliberately editable and outside the immutable artifact index; its packet hash binds it to that exact version. COMPLETE means packet creation succeeded, not review approval.

A responsible reviewer must identify themselves, record a timezone-aware review timestamp, and supply explicit decisions/evidence references for Indian provenance, research-use rights, privacy, labels, group containment and target definition. The current draft taxonomy must be intentionally accepted or revised through a new packet; a candidate label is not a reviewed label. Every record needs include/exclude and a rationale. Included records need a reviewed known family and complete redaction spans. Excluded records have no release label. No proposal spans are silently accepted. Empty spans mean the reviewer has actually checked that retaining the text is appropriate, not that an automatic detector found nothing.

Spans use Python Unicode character offsets into the exact bound original text: start inclusive, end exclusive. They must be sorted, non-overlapping and within bounds; booleans are not offsets. Replacement runs from right to left with `[REDACTED]`, preserving offsets. Reviewers must check sensitive context and indirect identifiers, not just obvious names/contact details. Completely removed content is rejected. Changed source text invalidates prior decisions.

After genuine review, run:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.release export --packet data/review/development-release-review-v1 --decisions data/review/development-release-review-v1/decisions.json --output data/review/reviewed-development-v1
```

The export contains only record/group IDs, redacted text, reviewed label and label origin; no reviewer identity, raw text, coordinates, source category or rationale is copied into model-facing records. IDs remain linkable pseudonyms, not anonymization. Keep every output private and ignored. Groups cannot be reassigned by the decision ledger. Conflicting included labels within a group and normalized identical redacted text crossing groups block export. A conflict requires upstream containment review/new packet, not silent merging or splitting here.

Exports are development-only, with `training_approved=false`, `evaluation_holdout=false` and operational approval false. The existing pilot has already been inspected and cannot be promoted to an untouched test set. Full-corpus near-duplicate/event review and a fresh independent reference set remain outstanding. This exporter does not establish statistical support or fold feasibility; those are separate checks.

## Trust and failure boundaries

Evidence references and reviewer declarations are accountable records, not cryptographic identity checks or proof of lawful use, exhaustive privacy review or semantic correctness. The local tool cannot establish that a claimed human review really occurred. Never populate these fields with invented review or have the assistant impersonate a human. AI proposals remain separate. Hashes detect stale/accidentally changed inputs, not a maliciously rewritten packet/index. No automated regex or span transformer certifies anonymity.

The command checks indexed upstream inputs and exact identity/text bindings. It refuses overwrites, outputs outside ignored `data/review`, overlapping input/output paths, missing decisions, unknown fields, false/missing gates and invalid spans. No original source is changed. Incomplete writes retain INCOMPLETE and are not accepted by downstream indexed readers. Errors omit raw complaint content. No production application, dependency, schema, model inference or API change is made.

Design references: [Presidio's handling of redaction and overlapping spans](https://microsoft.github.io/presidio/anonymizer/) informed explicit span handling; CivicAI deliberately rejects overlap for review rather than choosing one entity silently. [scikit-learn's leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) supports keeping development and untouched evaluation separate. No new package was needed.

## Next step

Complete substantive label/privacy/rights decisions for a development release without inventing independent human review, and resolve containment/context holds. If assistant-only weak supervision is chosen instead, predeclare that separately and preserve independent reference evaluation; do not relabel AI proposals as human-reviewed. Then implement a separately tested real-data loader only against an accepted release. The current training command still refuses all real releases.

## Verification

26 new tests; full research suite: **277 passed in 26.51s** (`python -m pytest research/tests -q -p no:cacheprovider --basetemp tmp/pytest-release-final`). Tests use invented fixtures and review attestations only. The actual pending packet was refused. OpenCity source checksum remains unchanged; application suites/builds were not rerun for this isolated research change.
