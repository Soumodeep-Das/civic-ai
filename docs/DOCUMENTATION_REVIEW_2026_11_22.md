# Repository documentation review — November 22, 2026

## Review scope

Reviewed GitHub `Soumodeep-Das/civic-ai` through the GitHub connector and the synchronized local checkout starting at `f2e7582`. Changes are documentation-only. No source code, migrations, configurations, datasets, labels, metrics, private artifacts or reference attachments were changed or deleted.

## Material inconsistencies corrected

| Finding | Correction |
|---|---|
| README simultaneously claimed a fitted classifier and no training/results | Replaced issue-by-issue introduction with current capabilities and a clearly bounded 97-text result |
| Architecture called implemented storage, authentication and inference future work | Rewrote current system/module map with workflow, sequence and logical data diagrams |
| Research landing page had several contradictory “Latest” sections | Added a single current entry point; retained source/curation commands and historical reports |
| Original eight-class taxonomy could be confused with the four-family model | Named the distinction and linked the actual protocol |
| Missing model in public clones was not prominent | Documented artifact prerequisites, disabled behavior and CI skip |
| Email instructions allowed disabled production transport | Documented deployed capture/disabled rejection and configured SMTP/Brevo requirement |
| Evidence described as municipal-only | Documented authorized staff and owning authenticated citizen access |
| Tracking contract promised 404 for missing/malformed token | Matched FastAPI query validation: 422 for missing/malformed, 404 for well-formed wrong capability |
| Readiness implied all providers were checked | Distinguished database/schema/storage from optional model/map/email/OIDC |
| Git workflow recommended branches despite owner-directed main workflow | Recorded current main-only publication convention |
| Failed sandbox socket probe was described as proof of stopped PostgreSQL | Corrected to unavailable connection evidence; actual service state was not established |
| CI success could imply private artifact inference was exercised | Explicitly recorded the private-artifact test's conditional skip |
| Minor comparison was written as if delivered | Distinguished original synopsis, delivered text experiment and unfinished image/multimodal objectives |
| Setup contained workstation-specific runtime paths | Replaced landing-page setup with portable prerequisites and ordered PowerShell commands |
| License status was unstated | Stated that no software license file is present; did not assign a license |

## Review boundaries

This is not a new security audit, model evaluation or production certification. Prior evidence is dated and identified by environment. Existing logs and issue documents are retained as history rather than rewritten to fabricate completion. The public beta was not mutated or declared equivalent to the local ML demonstration.

The old statement that the live map was freshly verified on November 21 was stronger than the captured evidence: the already-loaded page exposed map structure and prior state, while the new citizen reload hit a certificate warning. Treat the previous end-to-end November 21 verification as the live journey evidence; the later read-only inspection is not a new full journey.

## Verification for this change

Validation passed for 18 changed/new Markdown files: 90 relative link targets exist, code fences are paired, and six Mermaid blocks have the expected diagram structure. `git diff --check` passed. The final scope contains Markdown only, with no deleted files. Mermaid was checked structurally, not visually rendered in this review. No application tests or model training were rerun for prose edits; prior regression results remain dated evidence, not new results.
