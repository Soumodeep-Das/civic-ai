# Current State

## Issue #4 implemented and locally verified

Branch: feat/accessible-location-picker.

Issue #4 acceptance criteria and provider constraints are recorded in `ISSUE_004_LOCATION_SELECTION.md`. The implementation adds accessible issue-place search, current-location reuse, optional map refinement and truthful location precision. The citizen frontend requires a photo and confirmed location while the API/database remain compatible with existing optional records.

### Issue #4 backend checkpoint

Migration 0003 is applied to development PostgreSQL and adds nullable label, precision and nearby-detail fields without changing old rows. Complaint create/read/list expose the additions while remaining compatible with coordinate-only or location-free clients. `POST /api/v1/location-search` validates explicit queries and returns a normalized provider-neutral result contract. The Nominatim-compatible adapter enforces upstream pacing, caching, country configuration and sanitized failures.

### Issue #4 frontend checkpoint

The citizen form now requires a valid photo and a confirmed issue location. Users may search explicitly by place/PIN/street/landmark, choose a result without a map, use their current location, add nearby details, or open a lazy-loaded MapLibre map for pointer, marker-drag and keyboard refinement. Changing the point invalidates confirmation. Search, browser-position and map errors retain the rest of the form. Stored complaints display location label, precision and details when present.

Frontend verification: TypeScript compilation passes, all 20 interaction tests pass and the production build succeeds. Lazy loading reduced the initial JavaScript bundle from about 1.27 MB to 236 kB; the optional map chunk is about 1.03 MB and retains Vite's non-blocking large-chunk advisory. A live search for Baranagar Municipality returned a relevant result; selection without a map, optional map loading, keyboard adjustment, reconfirmation and mandatory-field feedback were exercised in the browser. No demonstration complaint was created during that check.

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

The Issue #3 checkpoint originally verified migration 0002 with 42 backend and 15 frontend tests. Issue #4 has advanced development PostgreSQL to migration 0003. The final combined regression passed 62 backend tests and 20 frontend tests; TypeScript compilation and the production build also passed. Three existing dependency deprecations, the known pytest cache warning and Vite's optional-map chunk-size advisory remain non-blocking.

Local availability was rechecked after the frontend development process stopped and produced a browser “site can't be reached” error. The backend remained healthy. `scripts/start-dev.ps1` now checks and starts the missing local services and verifies the Vite complaint API proxy before reporting readiness. The site and proxied complaint list were reachable again after using it.

Real browser: uploaded synthetic PNG, submitted without location, displayed image, submitted text after an actual location timeout, reloaded and confirmed both records remained. PostgreSQL confirmed the image reference and nullable coordinates. Browser console was clear.

Successful device location capture is now verified in the live browser. A complaint with optional photo and captured location was submitted; the UI shows it as location-provided, the API returns both coordinates, and the user independently confirmed the values in pgAdmin. Automated tests cover success, denial, timeout, unavailable API and late callbacks. An observed Windows registry consent value remained `Deny` even after capture succeeded, so it is not treated as authoritative for this desktop-browser flow; the browser API result is the operational check.

## References

API_CONTRACT.md describes multipart/search contracts and limits. ISSUE_003_EDGE_CASES.md and ISSUE_004_LOCATION_SELECTION.md record primary-source research and tradeoffs. DEVELOPMENT_LOG.md contains checkpoints. No production security, geocoding SLA, public deployment or research-results claim is made.
