# API Contract

Issue #1 source is implemented; runtime verification is pending.

| Method | Path | Success |
|---|---|---|
| GET | /health | 200, {"status":"ok"} |
| POST | /api/v1/complaints | 201, created complaint |
| GET | /api/v1/complaints/{complaint_id} | 200, complaint |
| GET | /api/v1/complaints | 200, array of complaints |

All endpoints are anonymous for local development. Listing returns all records ordered by created_at then UUID; no filtering or pagination.

## Creation request

```json
{"description":"Large pothole near the school entrance","latitude":22.5726,"longitude":88.3639}
```

Description is a required string, trimmed before storage. Empty and whitespace-only values fail validation. Latitude and longitude are independently optional/nullable with inclusive ranges [-90,90] and [-180,180]. Nonfinite coordinates fail. Extra fields are rejected, including client-supplied status, UUID, timestamps or future fields.

## Response

Exactly seven fields: complaint_id (generated UUID v4), description, latitude, longitude, status, created_at and updated_at. Status is restricted to submitted. PostgreSQL initializes both timestamps together. Responses serialize timezone-aware timestamps to ISO 8601 UTC ending in Z.

## Errors and health

- Unknown valid UUID: 404, {"code":"complaint_not_found","message":"Complaint not found"}.
- Invalid input or UUID: 422, {"code":"validation_error","message":"Invalid request","details":[...]}. Detail entries contain location, message and type; raw input is not echoed.
- Database operational error: 503, {"code":"database_unavailable","message":"Database temporarily unavailable"}.

GET /health is liveness only. DATABASE_URL is required at startup, but no connection is opened for health. FastAPI serves /docs and /openapi.json.

No update/delete routes, accounts, images, ML, category/priority/severity fields or routing exist in this issue.
