# API Contract

## Status

This is a design-level contract. No endpoint currently exists, and request or response examples must not be interpreted as implemented behavior. The first implementation issue may refine the complaint resource before coding.

## Conventions

- Base path: `/api/v1`
- Transport: HTTPS outside local development
- Payloads: JSON, except a future upload flow may use multipart requests or signed uploads
- Identifiers: opaque UUID strings
- Timestamps: ISO 8601 in UTC
- Errors: one consistent object containing a stable code, human-readable message, and optional field details
- Pagination: explicit page/cursor parameters and metadata; exact method unresolved

## Proposed resources

### Health

`GET /health` provides a minimal service health response. Readiness checks for dependencies should be separated if deployment requires them.

### Complaints

`POST /api/v1/complaints` creates a complaint from validated citizen input. The first vertical slice should accept text and optional location only if those fields are included in the reviewed domain model. Image upload, authentication, ML classification, and automatic priority are out of scope until separately designed.

`GET /api/v1/complaints/{complaint_id}` returns one complaint to an authorized caller.

`GET /api/v1/complaints` returns a paginated list for an authorized administrative caller, with filters introduced only when needed.

`PATCH /api/v1/complaints/{complaint_id}` may eventually update permitted workflow fields. Allowed state transitions and roles must be defined before implementation.

### Media

A media endpoint or signed-upload flow is expected later. File types, maximum size, malware handling, metadata stripping, access authorization, retention, and storage provider are unresolved; therefore no media route is committed yet.

### Inference

ML inference should initially be an internal backend service, not a public endpoint. The application may later expose prediction metadata as part of a complaint response, including model version and whether a human overrode the prediction.

## Proposed complaint representation

A response may eventually contain:

```json
{
  "complaint_id": "opaque-uuid",
  "description": "Citizen-provided description",
  "location": {"latitude": 0.0, "longitude": 0.0},
  "status": "submitted",
  "created_at": "ISO-8601 UTC timestamp",
  "classification": null,
  "priority": null
}
```

The numeric coordinates are illustrative shape values, not a real complaint. Null classification and priority make clear that those capabilities are not implied by record creation.

## Security and privacy requirements

- Administrative list/detail access must be authenticated and authorized before real data is used.
- Citizen access must not permit identifier enumeration or disclosure of other reporters' complaints.
- Rate limits, request-size limits, content validation, and audit events should be added according to threat and deployment needs.
- API logs should avoid raw complaint text, precise coordinates, tokens, and image contents by default.
- Public responses must not expose annotator, source-license, internal model, or reporter fields unintentionally.

## Contract evolution

Generate an OpenAPI description from the implemented FastAPI service, but keep this document focused on product-level behavior and boundaries. Breaking changes require a recorded decision, migration plan, and versioning assessment.

