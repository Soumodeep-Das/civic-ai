# Issue #12 — Production deployment and operational readiness

## Scope and decision

Issue #12 packages the existing product for a small, portable, single-server deployment. It does not add ML, cloud-specific infrastructure, Kubernetes, citizen accounts or automated routing. Research Stage B remains paused.

The selected topology is Docker Compose with Caddy, one FastAPI/Uvicorn service and PostgreSQL. It is small enough for an MCA project, reproducible on a normal Linux VPS, and separates the only public process from database/application networks. A one-shot migration service gates backend startup. Named volumes preserve PostgreSQL, evidence and Caddy state.

The bounded research used primary guidance: FastAPI's [proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/), [HTTPS](https://fastapi.tiangolo.com/deployment/https/), [Docker](https://fastapi.tiangolo.com/deployment/docker/) and [deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/) documentation; Docker's [Compose startup-order](https://docs.docker.com/compose/how-tos/startup-order/) and [official PostgreSQL image](https://hub.docker.com/_/postgres) guidance; Caddy's [trusted proxy](https://caddyserver.com/docs/caddyfile/options), [common patterns](https://caddyserver.com/docs/caddyfile/patterns) and [header](https://caddyserver.com/docs/caddyfile/directives/header) documentation; PostgreSQL's [`pg_dump`](https://www.postgresql.org/docs/16/app-pgdump.html) and [`pg_restore`](https://www.postgresql.org/docs/current/app-pgrestore.html) documentation; and OWASP guidance for [HTTP headers](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html), [logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), [file upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) and [CSP](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html). The PostgreSQL 18 volume is mounted at `/var/lib/postgresql`, matching the image's version-specific `PGDATA` contract rather than the pre-18 path. Research stopped after these sources resolved the topology and controls; no enterprise reference architecture was copied.

## Implemented production boundary

- Caddy terminates TLS, redirects HTTP, compresses responses, serves the Vite production bundle and proxies only backend paths.
- API paths are handled before SPA fallback; a missing API remains a JSON/API 404.
- Uvicorn trusts forwarded headers only from Caddy's fixed private address. Backend and PostgreSQL publish no host ports.
- The Python image is pinned to Python 3.12, runs as UID/GID 10001 and does not need source-code/Git write access.
- PostgreSQL, evidence and certificate state use separate persistent named volumes.
- `APP_ENV=production` rejects an insecure cookie, non-HTTPS allowed origins, weak/default tracking secret, invalid release/log level and a non-absolute evidence path.
- `.dockerignore` excludes secrets, runtime data, backups, research/raw data, ML/model artifacts, Git and developer dependencies.
- `/health` is liveness plus safe release ID. `/ready` checks PostgreSQL, exact Alembic head `0007` and writable evidence storage; it returns sanitized reasons and ignores the optional geocoder.
- SQLAlchemy retains bounded connection attempts and `pool_pre_ping`; the lifespan disposes the pool cleanly.
- Caddy limits request bodies to 6 MiB while the application validates/re-encodes JPEG/PNG evidence up to 5 MiB. Evidence remains outside the web root.
- Security headers are applied at proxy and application boundaries. Fingerprinted assets are immutable; HTML, authenticated responses and evidence are non-cacheable.
- JSON container logs rotate at five 10 MiB files per service. Application request logs carry timestamp/severity/request ID/method/normalized route/status/latency and exclude request bodies, raw path identifiers and secrets.
- Backup, disposable restore verification, dry-run media consistency audit, startup/shutdown and diagnostics commands are versioned.
- GitHub Actions runs Python/backend/research tests, migration, frontend tests/build and container/Compose build validation. It does not deploy.
- Leaflet map tiles use MapTiler Streets v4 through browser-public `VITE_MAPTILER_API_KEY`. The current one-key plan reuses `MAPTILER_API_KEY` through Compose; a separate override remains supported for future plans. Any browser-used value is publicly observable, is restricted by MapTiler Allowed HTTP Origins, and has no anonymous fallback. Compose sends `MAPTILER_REQUEST_ORIGIN` on backend geocoding so the origin-restricted shared key continues to work. The proxy build requires one of the key values and CSP permits only MapTiler's image origin.

## Mandatory citizen data exposure audit

The earlier anonymous global list exposed descriptions, precise locations, timestamps, UUIDs and evidence references. That was acceptable only for synthetic local demonstrations and is not defensible for production. Issue #12 deliberately changes the public contract:

| Context | Unauthenticated response |
|---|---|
| Submit complaint | The submitter receives their just-created record plus a 64-character HMAC capability token. `image_ref` is suppressed. This one response echoes submitted location so the user can confirm receipt. |
| Global complaint list | Disabled with 404; there is no public enumeration feed. |
| Status tracking with correct capability | Complaint UUID, description, status, created/updated timestamps only. |
| Missing/wrong capability | 404, avoiding existence disclosure. |
| Evidence URL | No anonymous access. Authentication and complaint-level municipal authorization are enforced server-side. |
| Department, assignee, internal note/history, accounts/audit | Never included in citizen contracts. |

Descriptions and full UUID/timestamps remain on the private capability page because they let an anonymous reporter identify and track the report. The token is generated from a production secret with HMAC-SHA-256 and compared in constant time; it is not stored in the database or logs. It is a bearer capability and must be saved privately. Exact coordinates, labels, nearby details, evidence and internal municipal activity are excluded from tracking responses. Rotating the secret invalidates all links.

This is an intentional privacy-driven breaking change, with updated UI and tests. It does not silently erase stored complaint data or municipal access.

## Evidence and upload review

Uploads keep the established collision-safe random filename, path validation, MIME/decoded-format/dimension checks, metadata-stripping re-encode and non-executable storage. PostgreSQL stores only a reference. The evidence volume is private and the backend route resolves a validated basename, authenticates the session, finds its complaint and reuses complaint authorization before returning `private, no-store` content.

`civicai.media_audit` compares database references and the evidence directory without deleting. A query failure is not interpreted as orphan proof. Object storage can later replace this adapter but is not forced into this portable milestone.

## Security review and explicit limits

The focused attack-surface review covered anonymous submission/status, evidence, admin/RBAC routes, session cookies, CSRF/origin enforcement, uploads, location proxy, request IDs, logs, secrets and build context. Production cookies retain Secure, HttpOnly, SameSite=Strict and Path `/`; no Domain is widened. Existing CSRF checks remain server-enforced. The CSP permits only current same-origin assets/API, data/blob previews and MapTiler's image origin; it has no `unsafe-eval`.

The current one-key MapTiler credential enters the frontend build through the Vite-facing variable and therefore cannot be considered server-secret. It is public by design and must be origin/usage restricted; a future multi-key plan can set a distinct frontend override. Source maps remain disabled. Caddy's 6 MiB body limit is deliberately above the valid 5 MiB image plus multipart fields.

## Production tile-provider defect

Final production-like verification exposed one isolated deployment defect: `VITE_MAP_TILE_URL` compiled the public `tile.openstreetmap.org` endpoint into the frontend, and that provider returned visible `Access blocked / 403` tiles. CivicAI does not bypass or spoof that policy. The production design now uses MapTiler Streets v4, the existing Leaflet interactions, required MapTiler/OpenStreetMap attribution, and a browser-public key. The present plan's single key supplies both geocoding and tiles; the configuration still accepts separate values later. MapTiler documents the raster URL and Leaflet settings in its [Leaflet integration](https://docs.maptiler.com/leaflet/), the attribution obligation in its [attribution guide](https://docs.maptiler.com/guides/map-design/attribution/add-attribution/), and browser-key restrictions in its [API key guide](https://docs.maptiler.com/guides/credentials/api-key/).

The current MapTiler account permits one active API key. The owner added `localhost` to that key's Allowed HTTP Origins without rotating it. The same ignored `.env.production` value now supplies backend geocoding and the Vite build; it is therefore publicly observable and protected by provider origin/usage restrictions rather than secrecy. The architecture still accepts a distinct `VITE_MAPTILER_API_KEY` if a later plan permits multiple keys. Human verification of the rebuilt HTTPS stack confirmed that geocoding and tiles both work and the old OSM 403 placeholders no longer appear.

Process-local login throttling does not become distributed merely through Compose. No new reverse-proxy rate limiter was added because reliable per-route Caddy limiting would require another maintained plugin/build and guessed thresholds could block operators. Host/provider controls and measured rate policies remain deployment work. The topology does not claim HA, zero downtime, legal retention compliance, external monitoring or a provider SLA.

## Verification record

- 185 Python tests passed: 129 backend and the unchanged 56 research tests. The output contains three recorded dependency deprecations plus the known local pytest-cache ACL warning.
- All 52 frontend tests passed; TypeScript and the Vite production build passed. The initial bundle is 246.27 kB (76.35 kB gzip), with lazy admin/map chunks. The bundle contains MapTiler Streets v4 and no `tile.openstreetmap.org` host; public source maps were not emitted.
- `pip check` reported no broken requirements. The production-only npm audit reported zero known vulnerabilities. No blanket dependency upgrade was performed.
- PowerShell scripts parse, Compose renders with placeholders, `git diff --check` passes and a focused final readiness/media suite passed 7/7 after the last change.
- The raw OpenCity file was re-hashed locally on 2026-10-03 and remained `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- A real native PostgreSQL `pg_dump --format=custom` was restored with `pg_restore --exit-on-error` into disposable database `civicai_restore_issue12_20261002_195619`. It was at `0007` and contained complaints, municipal users, departments, status/assignment histories and security events. Five evidence files were archived/restored with identical SHA-256 values; `civicai.media_audit` reported five database references, five files and no missing/orphan/invalid entry.
- The live development browser submitted a clearly synthetic photo/location complaint. Its receipt produced a private link; the page displayed only reference/description/status/timestamp and zero images, while explicitly withholding precise location/internal activity. Wrong capability returned 404; anonymous evidence returned 401. `/health` and `/ready` returned 200 with request ID and intended application headers.

The owner completed the final production-like verification through `https://localhost` after rebuilding the backend and proxy. Docker PostgreSQL, FastAPI and Caddy were healthy; administrator bootstrap/login and municipal features loaded; the intentionally fresh production database remained separate from development; citizen complaint submission and location search worked; MapTiler tiles rendered without the OSM access-blocked result; and the submitted complaint appeared in the municipal interface. No blocking browser issue remained. This verifies the documented single-host project deployment flow but is not formal production certification, penetration testing, high-availability validation, disaster-recovery certification or legal/regulatory approval.

## Deferred product improvements

Citizen notifications, richer signed-in citizen history/status, further map visual/interaction polish, and broader communication UX are explicitly outside Issue #12. They remain future product milestones and are not claimed here.

## Research isolation

No research code/data/decision was changed. `data/`, `research/`, `ml/` and `models/` are excluded from the container build context and never mounted or included by runtime backup scripts. The authoritative OpenCity raw SHA-256 was reverified as `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac` before completion.
