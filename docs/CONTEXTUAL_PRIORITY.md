# Contextual priority prototype v1

2026-11-20. Offline policy foundation; not connected to the API or UI. This is an experimental rule system, not a trained severity model or municipal SLA.

## Rubric declared before implementation

All inputs are explicit reported facts, never inferred from a category, photograph, map pin, sentiment, traffic, or submission timestamp. Each fact is yes/no/unknown/conflict. The current envelope attributes facts to one reporting source; combining sources requires explicit conflict reconciliation later.

In order: any conflict -> needs_review; reported immediate danger -> needs_review with emergency escalation flag (no dispatch promise); unknown immediate danger -> needs_review; reported access obstruction or essential-service interruption -> High; unknown access/service -> needs_review; otherwise Medium. No Low or Critical recommendation is assigned in v1. All results require staff review. Missingness is listed even when a known disruption justifies High.

Road/pedestrian example: reported blocked access can suggest High; a pothole photograph alone cannot. Waste: reported blocked access can suggest High; ordinary waste presence does not establish danger. Drainage: reported essential-service interruption can suggest High; water in a photo does not prove sewage. Lighting: a reported interruption can suggest High; daytime lamp appearance cannot establish failure. The same explicit-fact rules apply without forcing unsupported issues into the four classifier families. These examples are synthetic logic cases, not validated urgency labels.

No incident-duration or queue-age weighting until a defensible rubric exists. No automatic assignment/status change. No public endpoint, migration, citizen fields or deployment in this checkpoint. Next integrate durable attributed context and scoped municipal review with input fingerprints, keeping citizen claims distinct from municipal verification.

## Comparable-system research

[FixMyStreet guidance](https://www.llanfairparish.co.uk/shared/attachments.asp?f=6b9ea930-22fe-4d77-8598-f33e50b18653.pdf&o=FixMyStreet.pdf) separates urgent hazards from ordinary reporting because routing can delay action. Adopt the separation, not UK contact numbers or urgency standards. This is product-design research only, not training data. No foreign data enters the Indian ML experiment.

## Verification

Scenario tests exercise all 64 input combinations, deterministic output, missing/conflicting facts, invalid values and explicit provenance. These establish software behavior only; independent municipal validity remains unassessed.

## 2026-11-20 integration checkpoint

Migration 0010 adds complaint_priority_events with actor, complaint, timestamp and payload. Municipal-only GET /priority, POST /priority/context and POST /priority/reviews under the existing complaint route enforce complaint scope and CSRF for writes. Context/suggestion snapshots retain source, explanation, policy output and description hash; separate reviews reference a snapshot. Superseded/description-stale snapshots reject review (409); missing cross-complaint references return 404; accepting no suggestion returns 422. Complaint-row locking serializes context/review writes. No update/delete API; database-level immutability trigger and retry idempotency are not implemented. Repeating a successful write creates another event.

Municipal panel supports transcribed citizen or municipal reports, explicit unknown/conflict, preserved fact/history display and accept/correct/defer. Source is reported provenance, not independent verification. Corrections may record Low/Medium/High/Critical as staff decisions; policy itself emits only Medium/High or needs_review. No queue sorting, automatic status or dispatch changes.

Migration verified in isolated PostgreSQL test schemas only. Live Docker migration/rebuild/browser verification is pending. Do not claim this is already visible in the running Docker app. Use the existing backed-up start-ml-demo.ps1 workflow for local deployment verification.

## Citizen context collection

Migration 0011 and the citizen form collect immediate danger, public-access blockage and essential-service interruption as explicit `yes` / `no` / `unknown` reports. The answers are stored atomically as a `citizen_report` snapshot; they are not municipal verification. The citizen cannot select `conflict`, approve a recommendation or set an operational priority. Legacy API clients may omit all three; partial submissions fail rather than inventing missing facts.

When immediate danger is `yes`, the form explains that CivicAI does not dispatch help and points to 112. The [Ministry of Home Affairs ERSS page](https://www.mha.gov.in/emergency-response-support-system-erss) identifies 112 as India's nationwide unified emergency number. This safety guidance is not a priority label, response-time promise or external API integration. The complaint still persists so municipal evidence is not lost.

Automated verification covers anonymous provenance, all-or-none validation, invalid values, emergency review without status mutation, unknown preservation, multipart transport and the accessible emergency notice. Operational policy validity and citizen comprehension remain unassessed.
