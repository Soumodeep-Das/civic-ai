# Issue #4 — Accessible issue-location selection

Status: accepted and in progress on `feat/accessible-location-picker`.

## User outcome

The location represents the civic issue, not necessarily the reporter. A citizen can find the issue by locality, PIN code, street, address or landmark; use their current device location; optionally refine the selected point on a map; and add nearby plain-language details. Map interaction is never required for a search-based selection.

The citizen frontend requires a valid photo and a confirmed issue location before submission. The backend remains backward compatible: existing records and direct API clients may continue to omit media or location, and migrations remain additive and nullable.

## Acceptance criteria

- Explicit search only; no search-as-you-type requests.
- Query accepts 3–200 trimmed characters and returns at most five understandable results.
- Result selection works with keyboard and screen-reader semantics.
- Results identify `approximate` or `broad` precision instead of claiming an exact point.
- Current device location and map-adjusted pins use `exact` as the UI precision category, while remaining user-confirmed coordinates rather than surveyed positions.
- A selected search result can be confirmed without touching the map.
- The map is an optional adjustment surface: click or drag the marker, then confirm the revised point.
- Changing the search result, current-location capture or map point invalidates the previous confirmation.
- Photo and confirmed location are required by the citizen form. Errors focus on a corrective action and preserve other form inputs.
- Search timeout, provider failure, no results, ambiguous results, permission denial and slow requests are handled without losing the complaint draft.
- Existing complaint create/read/list and image behavior remains compatible; old rows continue to render.
- Search terms and coordinates are not written to application logs by CivicAI.

## Architecture and provider boundary

The React UI calls a CivicAI backend search endpoint. A small geocoding adapter calls a configured provider, normalizes results and maps provider-specific place types to CivicAI precision values. The browser never receives provider credentials. The first local-demonstration adapter uses Nominatim-compatible search with an identifying user agent, a one-request-per-second application limit, a small in-memory cache, explicit user-triggered requests and visible map/data attribution.

The provider base URL, country restriction and user agent are environment configuration. Provider failure returns a sanitized availability error. Public Nominatim is not a production SLA and may be replaced without changing the frontend contract.

The map renderer is separate from geocoding. MapLibre GL JS renders a compliant configured style/tiles source; it does not supply search data itself.

## Data additions

Migration 0003 adds nullable fields so existing data remains valid:

- `location_label`: selected human-readable result or current-location label.
- `location_precision`: `exact`, `approximate` or `broad`.
- `location_details`: optional nearby instructions supplied by the citizen.

New metadata is accepted only with both coordinates and a label/precision pair. Legacy coordinate-only records remain valid. These fields are application metadata and remain excluded from the current classification experiment.

## Research basis

- [FixMyStreet citizen experience](https://fixmystreet.org/pro-manual/citizens-experience/) supports address/place search or GPS followed by optional map refinement. Adopt the multi-path location flow, not unrelated routing or duplicate-report features.
- [W3C Geolocation](https://www.w3.org/TR/geolocation/) defines permission, timeout and cached-position behavior for current-location capture.
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) supplies an interactive TypeScript map renderer and marker controls but requires a separate tile/style and geocoding provider.
- [OSMF Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) permits moderate user-triggered searches but requires attribution and identification, caps use at one request per second, recommends caching/switchability and prohibits client-side autocomplete.
- [Google Places](https://developers.google.com/maps/documentation/places/web-service) is a future provider option with strong place search, but it requires credentials, billing and quota management; it is not selected for this local academic issue.

## Explicit exclusions

- No continuous location tracking, directions or navigation.
- No municipal boundary enforcement, department routing, duplicate detection or PostGIS.
- No automatic photo-EXIF location; downloaded images and screenshots often lack trustworthy metadata, and CivicAI strips image metadata.
- No Google Maps/Places account, key or billing configuration.
- No claim that public geocoding or public map tiles are production infrastructure.
