# API Contract

Issue #3 changes POST /api/v1/complaints to multipart/form-data. JSON creation now returns 415; clients must migrate. GET list/detail and health paths remain unchanged.

## Submission

Multipart fields: description (required trimmed nonempty text), latitude (optional number -90..90), longitude (optional number -180..180), image (optional JPEG/PNG file). Omit unavailable coordinates. Duplicate, unknown and server-owned fields are rejected. Do not set the Content-Type header manually in browser code; FormData supplies the boundary.

POST returns 201 with complaint_id, description, latitude, longitude, image_ref, status, created_at, updated_at. image_ref is null without an image, otherwise a relative /api/v1/complaint-images/<generated-name> URL. Status remains submitted; UUID and UTC timestamps remain server-owned.

## Reads

- GET /api/v1/complaints returns an array ordered by creation time then UUID.
- GET /api/v1/complaints/{complaint_id} returns the record or 404.
- GET /api/v1/complaint-images/{filename} returns validated raster content or 404. Names are restricted to generated hexadecimal UUIDs and jpg/png extensions.
- GET /health returns 200 {"status":"ok"} as liveness only.
- /docs and /openapi.json describe the multipart endpoint.

## Errors and limits

Errors use code/message, with details for field-validation errors. Invalid fields/images return 422, oversized uploads 413, wrong request media type 415, missing resources 404, and database unavailability 503.

Images: 5 MiB input and re-encoded output; 20 million pixels. Total multipart body: 5 MiB + 256 KiB. Non-file multipart parts: 64 KiB. One image maximum. MIME must match decoded JPEG/PNG format. Files are re-encoded without source metadata. Original filenames are ignored.

All endpoints, including images, are anonymous for local demonstrations. Do not expose this service publicly or submit private evidence until access controls and operational storage policy are designed.
