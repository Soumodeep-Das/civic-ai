# Current State

Issues #1 and #2 supplied the verified anonymous API and React complaint MVP.

## Issue #3 in progress

Branch: feat/complaint-images-location. Backend now accepts multipart complaints with optional JPEG/PNG evidence. Migration 0002 adds nullable image_ref without changing migration 0001. Existing coordinates remain optional.

Backend checkpoint: 38 tests passed before the final total-request-size guard; full rerun pending. Frontend integration, migration of the development database and real-browser verification are pending.

Manual coordinate inputs are being replaced with permission-based browser geolocation. Location is metadata only, excluded from the current minor-project classification experiment.

No ML, category, priority, severity, accounts, routing, maps or video is implemented.

See API_CONTRACT.md for the breaking POST media-type change and limits; DEVELOPMENT_LOG.md for evidence.
