# Current State

## Issue #4 implemented and locally verified

Branch: feat/accessible-location-picker.

Issue #4 acceptance criteria and provider constraints are recorded in `ISSUE_004_LOCATION_SELECTION.md`. The implementation adds accessible issue-place search, current-location reuse, optional map refinement and truthful location precision. The citizen frontend requires a photo and confirmed location while the API/database remain compatible with existing optional records.

### Issue #4 backend checkpoint

Migrations 0003 and 0004 are applied to development PostgreSQL without changing old rows. They add nullable label, precision, nearby details, selection source and device accuracy. Complaint create/read/list expose the additions while remaining compatible with coordinate-only or location-free clients. `POST /api/v1/location-search` and `POST /api/v1/location-reverse` use a normalized provider-neutral contract; `GET /api/v1/location-capabilities` tells the frontend whether autocomplete is allowed. The Nominatim fallback enforces explicit search, upstream pacing, caching, country configuration and sanitized failures. The MapTiler adapter enables autocomplete only when its server-side key is configured.

### Issue #4 frontend checkpoint

The citizen form now requires a valid photo and a confirmed issue location. Users may search by place/PIN/street/landmark, choose a result, use their current location, add nearby details, and refine the point on a lazy-loaded Leaflet street map. MapTiler mode provides 350 ms debounced autocomplete; Nominatim mode retains a visible Search button. Desktop left-click, marker drag and touch pan/zoom replace the directional controls. A moved pin is reverse-geocoded when possible, and changing any point invalidates confirmation. Search, browser-position, reverse-geocoding and map-tile errors retain the rest of the form.

Frontend verification: TypeScript compilation passes, all 24 interaction tests pass and the production build succeeds. The initial JavaScript bundle is about 238 kB and the lazy Leaflet map chunk is about 151 kB. MapTiler was configured locally through the ignored `.env` and verified through the running frontend: searching for Baranagar returned eight typeahead results, selecting one opened a detailed Leaflet/OpenStreetMap street map, and clicking the map moved the pin and reverse-geocoded the adjusted point to a nearby road/address. No location was confirmed and no demonstration complaint was created during that check. The key remains local and uncommitted.

The complete Issue #4 citizen workflow is now live-verified with a clearly labeled synthetic complaint. The browser accepted the description and PNG evidence, searched and selected Baranagar, adjusted the map pin, reverse-geocoded the point, accepted nearby details, required explicit confirmation, submitted successfully and increased the queue from eight to nine. API and direct PostgreSQL checks matched complaint `ecd45acb-63d3-42bd-b295-c758ac17694b`, including submitted status, image reference, coordinates, exact precision, map source, location label/details and timestamps. The stored image endpoint returned HTTP 200 as `image/png`. The demonstration record remains in the local development database.

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

The Issue #3 checkpoint originally verified migration 0002 with 42 backend and 15 frontend tests. Issue #4 has advanced development PostgreSQL to migration 0004. The final combined regression was rerun after the live end-to-end submission: 79 backend tests and 24 frontend tests passed; TypeScript compilation and the production build also passed; Alembic reports `0004 (head)`. Three existing dependency deprecations and the known pytest cache-permission warning remain non-blocking.

Local availability was rechecked after the frontend development process stopped and produced a browser “site can't be reached” error. The backend remained healthy. `scripts/start-dev.ps1` now checks and starts the missing local services and verifies the Vite complaint API proxy before reporting readiness. The site and proxied complaint list were reachable again after using it.

A host-level listener remained on the default backend port even though its earlier process ID was no longer addressable. Local `.env` now selects port 8001; the startup helper and Vite development proxy share `BACKEND_PORT`, while the tracked default stays 8000. Health, complaints, provider capabilities, MapTiler search and reverse lookup were all verified through the frontend proxy on port 5173.

Real browser: uploaded synthetic PNG, submitted without location, displayed image, submitted text after an actual location timeout, reloaded and confirmed both records remained. PostgreSQL confirmed the image reference and nullable coordinates. Browser console was clear.

Successful device location capture is now verified in the live browser. A complaint with optional photo and captured location was submitted; the UI shows it as location-provided, the API returns both coordinates, and the user independently confirmed the values in pgAdmin. Automated tests cover success, denial, timeout, unavailable API and late callbacks. An observed Windows registry consent value remained `Deny` even after capture succeeded, so it is not treated as authoritative for this desktop-browser flow; the browser API result is the operational check.

## References

API_CONTRACT.md describes multipart/search contracts and limits. ISSUE_003_EDGE_CASES.md and ISSUE_004_LOCATION_SELECTION.md record primary-source research and tradeoffs. DEVELOPMENT_LOG.md contains checkpoints. No production security, geocoding SLA, public deployment or research-results claim is made.
