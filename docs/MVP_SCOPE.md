# MVP Scope

## Product goal

Deliver one complete, demonstrable local workflow before adding broader synopsis features:

1. A person describes a civic problem and may provide coordinates.
2. The frontend submits the anonymous complaint through the API.
3. PostgreSQL stores the complaint.
4. The frontend shows the stored complaint in the recent-complaints queue.

This is the sole implementation focus until the workflow is verified end to end and documented.

## MVP components

- React and TypeScript web interface.
- FastAPI anonymous complaint API.
- PostgreSQL complaint persistence managed by Alembic.
- Complaint form, client-side validation, loading/empty/success/error states, and complaint list.
- Automated backend and frontend tests for the critical path.

## MVP completion criteria

- Both applications can be set up and started using README commands.
- A valid complaint can be submitted from the browser and survives a list refresh.
- Empty descriptions and invalid coordinates are rejected clearly.
- A backend-unavailable condition produces a useful message without losing entered complaint text.
- Backend and frontend automated tests pass.
- The production frontend build succeeds.
- Documentation matches the demonstrated behavior.

## Explicitly deferred

- User accounts, authentication and authorization.
- Images, camera input and file storage.
- Maps, automatic geolocation and address lookup.
- Category classification, severity, prioritization and ML inference.
- Department routing and workflow/status management.
- Administrative analytics, notifications and deployment.
- Research experiments, datasets, metrics and paper findings.

Deferred items are not abandoned; they may become later issues only after the MVP is accepted.
