# API Contract

Issue #3 changed POST /api/v1/complaints to multipart/form-data. Issue #4 adds optional location context to that compatible multipart contract and introduces explicit location search. JSON complaint creation still returns 415. GET list/detail and health paths remain unchanged.

## Submission

Multipart fields: description (required trimmed nonempty text), latitude (optional number -90..90), longitude (optional number -180..180), image (optional JPEG/PNG file), location_label (optional nonempty string, 300 characters), location_precision (optional `exact`, `approximate` or `broad`) and location_details (optional nonempty string, 500 characters). Omit unavailable coordinates. If any location-context field is sent, both coordinates plus label and precision are required. Coordinate-only legacy clients remain valid. Duplicate, unknown and server-owned fields are rejected. Do not set the Content-Type header manually in browser code; FormData supplies the boundary.

POST returns 201 with complaint_id, description, latitude, longitude, image_ref, location_label, location_precision, location_details, status, created_at and updated_at. image_ref is null without an image, otherwise a relative /api/v1/complaint-images/<generated-name> URL. Status remains submitted; UUID and UTC timestamps remain server-owned.

The citizen Issue #4 frontend requires a photo and confirmed location. The API intentionally keeps both optional for existing records, compatibility and non-browser clients; frontend policy must not be described as a database invariant.

## Issue-location search

`POST /api/v1/location-search` accepts JSON `{ "query": "Baranagar Municipality" }`. Query is trimmed, must contain 3–200 characters and rejects extra fields. The endpoint is explicit-submit search, not autocomplete.

Success returns up to five normalized results with provider_id, label, latitude, longitude and precision (`approximate` or `broad`). Search providers never return `exact`; only a user-confirmed device position or adjusted map pin receives that UI category. An empty array means no match. Provider timeout/failure returns 503 with code `location_search_unavailable` and a sanitized retry message.

The initial provider adapter is Nominatim-compatible, country-restricted through configuration, limited to one upstream request per second and cached in memory for 15 minutes. The provider receives the search text; users should search public places rather than private information. No search query or coordinates are intentionally written to CivicAI application logs.

## Reads

- GET /api/v1/complaints returns an array ordered by creation time then UUID.
- GET /api/v1/complaints/{complaint_id} returns the record or 404.
- GET /api/v1/complaint-images/{filename} returns validated raster content or 404. Names are restricted to generated hexadecimal UUIDs and jpg/png extensions.
- GET /health returns 200 {"status":"ok"} as liveness only.
- /docs and /openapi.json describe the multipart endpoint.

## Errors and limits

Errors use code/message, with details for field-validation errors. Invalid fields/images return 422, oversized uploads 413, wrong request media type 415, missing resources 404, and database unavailability 503.

Images: 5 MiB input and re-encoded output; 20 million pixels; single frame only. Total multipart body: 5 MiB + 256 KiB. Non-file multipart parts: 64 KiB. One image maximum. MIME must match decoded JPEG/PNG format. Files are re-encoded without source metadata, preserving orientation. Original filenames are ignored. Storage unavailability returns 503.

All endpoints, including images, are anonymous for local demonstrations. Do not expose this service publicly or submit private evidence until access controls and operational storage policy are designed.
