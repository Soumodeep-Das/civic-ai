# Current State

## Issue #3 implemented; device location verification remains limited

Branch: feat/complaint-images-location.

- Anonymous multipart complaint creation with optional JPEG/PNG evidence.
- Nullable image_ref added by migration 0002; original migration unchanged.
- Local images in data/uploads/complaints (UPLOAD_DIR override); bytes are not stored in PostgreSQL.
- Citizen form has optional photo selection/removal and one-shot browser geolocation, without manual coordinate fields.
- Location denial, unavailable browser, timeout and omission permit submission.
- Complaint list displays image evidence and friendly location confirmation.
- Coordinates remain metadata, excluded from the current minor-project classification experiment.
- No ML, category, priority, severity, accounts, routing, maps or video.

## Verification

Development migration is at 0002 (head). Four pre-existing complaints survived migration. Backend suite: 42 passing tests. Frontend suite: 15 passing tests. Production frontend build passes. Three pre-existing dependency deprecations remain non-blocking.

Real browser: uploaded synthetic PNG, submitted without location, displayed image, submitted text after an actual location timeout, reloaded and confirmed both records remained. PostgreSQL confirmed the image reference and nullable coordinates. Browser console was clear.

Successful device location capture and a visible browser permission-denial prompt could not be verified on this device; automated tests cover success, denial, timeout, unavailable API and late callbacks. This is an outstanding manual verification item.

## References

API_CONTRACT.md describes the multipart breaking change and limits. ISSUE_003_EDGE_CASES.md records primary-source research and tradeoffs. DEVELOPMENT_LOG.md contains checkpoints. No production security, public deployment or research-results claim is made.
