# Issue #4 — Accessible issue-location selection

Status: accepted; interaction refinement in progress on `feat/accessible-location-picker`.

## User outcome

The location represents the civic issue, not necessarily the reporter. A citizen can find the issue by locality, PIN code, street, address or landmark; use their current device location; optionally refine the selected point on a map; and add nearby plain-language details. Map interaction is never required for a search-based selection.

The citizen frontend requires a valid photo and a confirmed issue location before submission. The backend remains backward compatible: existing records and direct API clients may continue to omit media or location, and migrations remain additive and nullable.

## Acceptance criteria

- With a provider that explicitly supports autocomplete, debounce search-as-you-type requests and show up to eight understandable suggestions. The Nominatim fallback remains explicit-submit only.
- Query accepts 3–200 trimmed characters.
- Result selection works with keyboard and screen-reader semantics.
- Results identify `approximate` or `broad` precision instead of claiming an exact point.
- Current device location and map-adjusted pins use `exact` as the UI precision category, while remaining user-confirmed coordinates rather than surveyed positions.
- Selecting a suggestion opens a detailed street map centred on its point.
- Desktop users can left-click or drag the marker; touch users can pan/zoom the map and drag the marker. Directional nudge buttons are not part of the primary interface.
- Reverse-geocode a moved pin so the label and coordinates remain consistent; provider failure retains the point and clearly reports that its label could not be refreshed.
- Changing the search result, current-location capture or map point invalidates the previous confirmation.
- Photo and confirmed location are required by the citizen form. Errors focus on a corrective action and preserve other form inputs.
- Search timeout, provider failure, no results, ambiguous results, permission denial and slow requests are handled without losing the complaint draft.
- Existing complaint create/read/list and image behavior remains compatible; old rows continue to render.
- Search terms and coordinates are not written to application logs by CivicAI.

## Architecture and provider boundary

The React UI calls CivicAI backend search and reverse-geocoding endpoints. A small geocoding adapter calls a configured provider, normalizes results and maps provider-specific place types to CivicAI precision values. Provider credentials stay on the backend. The local-demonstration fallback uses Nominatim-compatible explicit search with an identifying user agent, a one-request-per-second application limit, a small in-memory cache and visible attribution.

MapTiler is the selected autocomplete and reverse-geocoding adapter. It is enabled only when `GEOCODING_PROVIDER=maptiler` and a non-empty `MAPTILER_API_KEY` are configured. The frontend reads a CivicAI capability endpoint before enabling debounced typeahead, so it never generates autocomplete traffic against the public Nominatim fallback. Country and optional proximity bias remain environment configuration.

The provider base URL, country restriction and user agent are environment configuration. Provider failure returns a sanitized availability error. Public Nominatim is not a production SLA and may be replaced without changing the frontend contract.

The map renderer is separate from geocoding. MapLibre GL JS renders OpenFreeMap's detailed Liberty street style by default; it does not supply search data itself. OpenFreeMap requires attribution and offers no SLA, so the style remains replaceable through frontend configuration.

## Data additions

Migration 0003 adds nullable fields so existing data remains valid:

- `location_label`: selected human-readable result or current-location label.
- `location_precision`: `exact`, `approximate` or `broad`.
- `location_details`: optional nearby instructions supplied by the citizen.

New metadata is accepted only with both coordinates and a label/precision pair. Legacy coordinate-only records remain valid. These fields are application metadata and remain excluded from the current classification experiment.

Migration 0004 will add nullable `location_source` (`search`, `device` or `map`) and `location_accuracy_m`. Device accuracy is stored only when the browser supplies a finite non-negative value. Map adjustment changes the source to `map` and clears device accuracy. Existing rows remain valid with both fields null.

## Research basis

- [FixMyStreet citizen experience](https://fixmystreet.org/pro-manual/citizens-experience/) supports address/place search or GPS followed by optional map refinement. Adopt the multi-path location flow, not unrelated routing or duplicate-report features.
- [W3C Geolocation](https://www.w3.org/TR/geolocation/) defines permission, timeout and cached-position behavior for current-location capture.
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) supplies an interactive TypeScript map renderer and marker controls but requires a separate tile/style and geocoding provider.
- [OSMF Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) permits moderate user-triggered searches but requires attribution and identification, caps use at one request per second, recommends caching/switchability and prohibits client-side autocomplete.
- [MapTiler geocoding API](https://docs.maptiler.com/cloud/api/geocoding/) explicitly supports autocomplete, fuzzy matching, country filters, proximity bias, reverse geocoding and up to ten results. Adopt its capabilities behind the existing provider boundary rather than exposing its key to the browser.
- [OpenFreeMap quick start](https://openfreemap.org/quick_start/) documents a detailed MapLibre-compatible Liberty style with automatic attribution. Use it for the academic prototype while recording its lack of an SLA.
- [Google Places](https://developers.google.com/maps/documentation/places/web-service) is a future provider option with strong place search, but it requires credentials, billing and quota management; it is not selected for this local academic issue.

## Explicit exclusions

- No continuous location tracking, directions or navigation.
- No municipal boundary enforcement, department routing, duplicate detection or PostGIS.
- No automatic photo-EXIF location; downloaded images and screenshots often lack trustworthy metadata, and CivicAI strips image metadata.
- No Google Maps/Places account, key or billing configuration.
- No promise that public OpenFreeMap tiles or a free MapTiler account are production municipal infrastructure.
- No claim that public geocoding or public map tiles are production infrastructure.
