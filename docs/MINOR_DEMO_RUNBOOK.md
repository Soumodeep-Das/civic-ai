# CivicAI minor-project demonstration runbook

Prepared 2026-11-21 for the November 27 presentation. This is a rehearsal/fallback guide, not production certification or an authorization to add last-minute features.

## Demonstration claim

CivicAI demonstrates a complete human-reviewed civic complaint workflow:

1. a citizen submits a description, protected photograph, confirmed issue location and three reported context answers;
2. the complaint persists in PostgreSQL and receives a private tracking capability;
3. authorized municipal staff inspect the original evidence;
4. a small experimental **text-only** classifier suggests one of four supported civic families or requests review;
5. a separate transparent rules policy suggests priority from the citizen's reported danger/access/service facts;
6. staff accept, correct or defer suggestions with an explanation; and
7. ordinary assignment/status/history and citizen tracking continue independently of ML/AI availability.

The photograph is evidence for staff. It is not consumed by the current model. Neither classification nor policy output automatically changes status, assignment, routing or dispatch.

## Day-before preparation

- Freeze `main` after a successful Quality gates workflow. Do not upgrade dependencies or add providers/models afterward.
- Run the backup-first local launcher from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-ml-demo.ps1
```

- Confirm the launcher reports a backup, migrations, healthy database/Mailpit/backend/proxy and readiness 200.
- Open `https://localhost/` and `https://localhost/municipal` in the exact Chrome profile used for the presentation. Resolve the expected local certificate trust prompt manually before presentation day; automation must not bypass it.
- Sign in to the municipal account once and confirm the existing verified demo complaint is available. Do not put its password, session cookie or private tracking token into slides, notes or Git.
- Keep one clearly synthetic, non-personal JPEG/PNG under 5 MiB ready. Avoid faces, number plates, private addresses and copied real complaint evidence.
- Keep the computer powered, Docker Desktop running and network available for MapTiler. The stored complaint workflow remains usable if experimental model generation is disabled; the map/provider is the main external visual dependency.

## Live demonstration sequence

### 1. Citizen report

Use an obviously synthetic but realistic description such as a blocked drain obstructing a public footpath. State aloud that the example is demonstration data.

- Enter the description.
- Upload the prepared synthetic photograph.
- Search for a public landmark/locality, select a result, inspect the pin and confirm the issue location.
- Answer the three reported-context questions. Use `No` immediate danger, `Yes` public access blocked and `Not sure` essential-service interruption for the clearest safe policy example.
- Submit and point out the UUID/private tracking link. Do not show or copy the full capability token into the presentation material.

If immediate danger is demonstrated, explain that CivicAI shows India's official 112 guidance and requests review; it does not dispatch emergency services.

### 2. Municipal evidence and ML review

- Open the newly submitted complaint from the authenticated municipal queue.
- Show the description, protected photo, MapTiler map and `citizen report` context provenance.
- Generate the experimental text assessment. Explain that its four-family model was developed from 97 Bengaluru complaint texts with AI-proposed labels; the grouped development macro-F1 comparison is exploratory, not independent accuracy or all-India validation.
- Accept, correct or defer it with a short explanation. Refresh and show that review history persists.
- Show the separate contextual priority suggestion. Explain the exact reported facts and unknown value. Accept/correct/defer with an explanation, then refresh.
- Point out that the complaint status remains `Submitted` until a staff member deliberately changes it.

### 3. Ordinary municipal workflow and citizen view

- Optionally assign the complaint to a demonstration department/operator and advance it to `Under review` with a non-sensitive internal note.
- Open the private citizen tracking view and show the public-safe status. Explain that internal notes, staff identity, exact location and photo are not exposed through anonymous tracking.

Do not modify a genuine complaint for the demonstration. If a new write fails, stop retrying and use the verified stored demo complaint rather than creating duplicates.

## Failure demonstrations worth explaining

- Wrong tracking token returns 404 so complaint existence is not disclosed.
- Public complaint-directory access returns 404; there is no global anonymous feed.
- Anonymous municipal access returns 401.
- Unsupported/ambiguous classifier input can request review; model failure never blocks complaint submission or staff work.
- Unknown/conflicting priority facts require review rather than being treated as safe/low.
- Provider/device location failure preserves the citizen's draft and leaves explicit search available.

These can be described from tested behavior; do not deliberately stop the database, corrupt evidence or change credentials during the presentation.

## Honest viva boundaries

- **Implemented:** protected complaint evidence/location, accounts/private tracking, municipal RBAC/workflow, experimental four-family text suggestion, transparent reported-context priority and staff review histories.
- **Not implemented/validated:** image classification, image severity, multimodal performance, independent accuracy, operational triage validation, emergency dispatch, all-India/West Bengal generalization, live traffic, automatic department routing, chatbot and formal production certification.
- The OpenCity source is Indian/Bengaluru; the raw checksum is `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- The priority component is a versioned rule system, not ML. Classification, visible evidence, severity and priority are separate concepts.
- The major-project path is better Indian/West Bengal coverage, independently labelled images and genuine paired text-photo evaluation—not an untested generic vision API.

## Fallback order

1. Use the already stored verified complaint in the municipal UI to demonstrate evidence, map, citizen context and persisted review history.
2. Use the existing research result document and architecture diagram to explain the reproducible text experiment if fresh inference is unavailable.
3. Use a locally stored screen recording only as a final fallback; label it as prerecorded and retain the actual timestamps/environment.

Never invent a live result, metric or successful request when a component is unavailable.
