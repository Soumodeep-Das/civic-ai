# MVP Scope

Issue #3 expands the accepted basic complaint MVP with optional photo evidence and browser location.

1. Enter a required description.
2. Optionally select one JPEG/PNG photo.
3. Optionally request current browser location with permission, while near the problem.
4. Submit even when location is unavailable.
5. Store text, nullable coordinates and image reference; show the stored complaint and image.

Manual coordinate entry is removed from citizen UX. Coordinates remain optional backend metadata for later geospatial work, not input to the current minor-project classification experiment.

## Acceptance

Tests and frontend build pass; migration preserves existing records. Verify text and image submissions, location success/failure, submission without location, persisted list after reload and understandable errors. Record device/browser limitations honestly.

## Deferred

Video, accounts, authentication, maps/address lookup, classification, priority, severity, department routing, analytics, notifications, deployment and research experiments. These require later issues and must not start automatically.
