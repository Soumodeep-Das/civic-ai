# Current State

## Issue #4 in progress after verified Issue #3

Branch: feat/accessible-location-picker.

Issue #4 acceptance criteria and provider constraints are recorded in `ISSUE_004_LOCATION_SELECTION.md`. Implementation will add accessible issue-place search, current-location reuse, optional map refinement and truthful location precision. The citizen frontend will require a photo and confirmed location while the API/database remain compatible with existing optional records.

### Verified Issue #3 baseline

- Anonymous multipart complaint creation with optional JPEG/PNG evidence.
- Nullable image_ref added by migration 0002; original migration unchanged.
- Local images in data/uploads/complaints (UPLOAD_DIR override); bytes are not stored in PostgreSQL.
- Citizen form has optional photo selection/removal and one-shot browser geolocation, without manual coordinate fields.
- Location denial, unavailable browser, timeout and omission permit submission.
- Location acquisition accepts a device fix up to five minutes old and waits up to 30 seconds; timeout guidance distinguishes browser permission from device provider availability.
- Complaint list displays image evidence and friendly location confirmation.
- Coordinates remain metadata, excluded from the current minor-project classification experiment.
- No ML, category, priority, severity, accounts, routing, maps or video.

## Verification

Development migration is at 0002 (head). Four pre-existing complaints survived migration. Backend suite: 42 passing tests. Frontend suite: 15 passing tests. Production frontend build passes. Three pre-existing dependency deprecations remain non-blocking.

Local availability was rechecked after the frontend development process stopped and produced a browser “site can't be reached” error. The backend remained healthy. `scripts/start-dev.ps1` now checks and starts the missing local services and verifies the Vite complaint API proxy before reporting readiness. The site and proxied complaint list were reachable again after using it.

Real browser: uploaded synthetic PNG, submitted without location, displayed image, submitted text after an actual location timeout, reloaded and confirmed both records remained. PostgreSQL confirmed the image reference and nullable coordinates. Browser console was clear.

Successful device location capture is now verified in the live browser. A complaint with optional photo and captured location was submitted; the UI shows it as location-provided, the API returns both coordinates, and the user independently confirmed the values in pgAdmin. Automated tests cover success, denial, timeout, unavailable API and late callbacks. An observed Windows registry consent value remained `Deny` even after capture succeeded, so it is not treated as authoritative for this desktop-browser flow; the browser API result is the operational check.

## References

API_CONTRACT.md describes the multipart breaking change and limits. ISSUE_003_EDGE_CASES.md records primary-source research and tradeoffs. DEVELOPMENT_LOG.md contains checkpoints. No production security, public deployment or research-results claim is made.
