# Decision Log

Only decisions actually made are recorded here. Proposed choices remain in the relevant design document until accepted. Each future entry should include context, decision, consequences, status, and date.

## D001 Separate classification from prioritization

- Date: 2026-09-19
- Status: accepted
- Decision: Complaint category classification and complaint prioritization are separate tasks. Category alone will not determine priority.
- Consequence: Data labels, model outputs, API fields, evaluation, and user explanations must preserve this distinction.

## D002 Minor research uses modality comparison

- Date: 2026-09-19
- Status: accepted
- Decision: The minor-project research will compare text-only, image-only, and text-image multimodal classification under controlled evaluation.
- Consequence: The dataset and split design must support fair aligned comparisons. No modality is presumed superior.

## D003 Transparent priority now and learned context later

- Date: 2026-09-19
- Status: accepted
- Decision: The approved prototype includes a separate, transparent contextual priority mechanism with human verification. Learned ranking and richer spatial-temporal prioritization are future major-project research.
- Consequence: The minor implementation may add documented scoring only after category and priority labels are defined; it must not be presented as validated ML without evidence.

## D004 Technology direction

- Date: 2026-09-19
- Status: accepted as direction
- Decision: Use React for the frontend, Python with FastAPI for the backend, PostgreSQL for persistence, and Python ML libraries selected according to experimental need.
- Consequence: A material change requires a new decision entry that explains benefits, drawbacks, and migration impact.

## D005 Milestone-driven delivery

- Date: 2026-09-19
- Status: accepted
- Decision: Build through small, reviewed vertical slices. The first planned slice is complaint submission through API and database persistence to an administrative list.
- Consequence: No full-stack or ML scaffolding is created during the foundation task.

## D006 Evidence and research integrity

- Date: 2026-09-19
- Status: accepted
- Decision: Citations, dataset rights, labels, metrics, findings, statistical claims, and novelty statements must be traceable to verified sources or reproducible project outputs.
- Consequence: Placeholder or invented results are prohibited, and limitations must be reported.
