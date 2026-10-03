# Production deployment

## Supported topology

```text
browser
  -> Caddy :80/:443 (TLS, headers, body limit, static React bundle)
     -> FastAPI/Uvicorn :8000 (private Compose network)
        -> PostgreSQL :5432 (private Compose network)
        -> evidence_data named volume
```

Only Caddy publishes host ports. PostgreSQL and Uvicorn are not public. Caddy builds and serves `frontend/dist`; Vite is never used at runtime. The backend image runs as UID/GID `10001`, writes only the evidence volume, and has no research-data mount. Caddy and PostgreSQL use their official non-root/container defaults where applicable.

The package targets a normal Linux host with Docker Engine and Compose v2. Windows remains supported for development and for driving these PowerShell helpers, but the deployed containers are Linux containers.

## Host prerequisites

- a DNS name resolving to the host;
- inbound TCP 80/443 and UDP 443 permitted;
- Docker Engine and `docker compose`;
- enough separately monitored space for Docker volumes and off-host backups.

Caddy obtains and renews a public certificate when the configured DNS name is reachable. Do not expose Uvicorn directly. Localhost uses Caddy's private CA and is suitable only when that CA is explicitly trusted by the test client; never click through a certificate warning.

## Configure once

From the repository root:

```powershell
Copy-Item .env.production.example .env.production
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()
```

Generate separate random values for `POSTGRES_PASSWORD` and `PUBLIC_TRACKING_SECRET`, then edit `.env.production`. Use URL-safe hexadecimal for the database password because it is interpolated into a SQLAlchemy URL. Set:

- `CIVICAI_SITE_ADDRESS` to the real DNS name (no path);
- `AUTH_ALLOWED_ORIGINS` to the exact `https://` origin;
- `RELEASE_ID` to the deployed Git commit SHA;
- `MAPTILER_API_KEY` for geocoding and, on the current one-key plan, frontend tiles;
- optional `VITE_MAPTILER_API_KEY` only when a future plan permits a distinct browser key.

`.env.production` is ignored. Never put credentials in Compose YAML, shell history, images, screenshots, logs, or Git. With the current single-key MapTiler plan, leave `VITE_MAPTILER_API_KEY` empty: Compose supplies `MAPTILER_API_KEY` to both backend geocoding and the Vite build. That shared value is visible in the compiled bundle and browser network requests, so it is not secret. In MapTiler, add `localhost` (without protocol or port) to Allowed HTTP Origins for local production-like verification and restrict real deployment to the actual CivicAI domain. Compose derives `MAPTILER_REQUEST_ORIGIN=https://CIVICAI_SITE_ADDRESS` so origin-restricted server geocoding identifies the same application origin. MapTiler's localhost rule is only a usage control and cannot authenticate a local machine. If the plan later permits multiple keys, set `VITE_MAPTILER_API_KEY` to a distinct browser-restricted value without changing code.

Validate without starting:

```powershell
docker compose --env-file .env.production -f compose.production.yml config --quiet
```

## First deployment and routine release

Before every release, follow [BACKUP_RESTORE.md](BACKUP_RESTORE.md). Then:

```powershell
.\scripts\start-production.ps1
```

The one command builds immutable frontend/backend images, waits for PostgreSQL, runs `alembic upgrade head` once, starts the backend only if migration succeeds, waits for `/ready`, and then starts Caddy. A failed migration or readiness probe makes startup fail rather than presenting a false success.

Verify:

```powershell
docker compose --env-file .env.production -f compose.production.yml ps
curl.exe --fail --show-error https://YOUR_DOMAIN/health
curl.exe --fail --show-error https://YOUR_DOMAIN/ready
.\scripts\diagnose-production.ps1
```

Then perform one synthetic citizen submission and the municipal checks in the deployment checklist below. Research data is never demo data. Create the first administrator interactively inside the private backend container:

```powershell
docker compose --env-file .env.production -f compose.production.yml exec backend python -m civicai.bootstrap_admin
```

The password prompt is interactive; no password belongs in `.env.production` or Compose.

Clean shutdown retains all named volumes:

```powershell
.\scripts\stop-production.ps1
```

Never add `--volumes` unless the exact data-destruction operation has been separately approved and backed up.

## Deployment checklist

1. Confirm the intended Git commit; set the same `RELEASE_ID`.
2. Review `.env.production` permissions and placeholders without printing values.
3. Create and verify database plus evidence backups.
4. Build and start with `start-production.ps1`; do not run Alembic concurrently elsewhere.
5. Confirm all Compose services are healthy and `/ready` returns 200.
6. Confirm `/health` reports the intended release.
7. Load `/`, `/admin`, `/admin/complaints`, `/admin/users`, a complaint detail route and a nonexistent UI route.
8. Submit a clearly synthetic complaint with synthetic image/location.
9. Save its private tracking link; confirm another/no token gets 404.
10. Sign in over HTTPS; inspect its evidence; confirm unauthenticated evidence returns 401.
11. Confirm CSRF rejects a bad origin/token and ordinary admin mutations work.
12. Exercise department assignment, self-claim (as applicable), status update, reload and logout.
13. Inspect response security/cache headers and request IDs.
14. Inspect bounded container logs for failures and prohibited complaint/credential content.
15. Record release, backup identifier and smoke-test result outside the repository.

## Proxy and trust boundary

Uvicorn accepts forwarded headers only from `172.28.0.10`, Caddy's fixed private-network address. The backend has no published port. Caddy uses strict trusted-proxy parsing. This fixed subnet is part of the Compose contract; changing it requires changing the Uvicorn trust setting too. Never use `--forwarded-allow-ips=*` on a publicly reachable backend.

Caddy routes `/api/*`, `/health` and `/ready` to FastAPI before SPA handling, so API 404s stay API 404s. Fingerprinted `/assets/*` are immutable; `index.html`, admin responses and protected evidence are not cached. Public source maps are not emitted by the Vite production build.

## External providers

Geocoding uses the configured backend provider. With the current one-key plan, Compose also passes `MAPTILER_API_KEY` into the Vite-facing `VITE_MAPTILER_API_KEY`, so it is publicly observable and must be origin/usage restricted. The backend includes `MAPTILER_REQUEST_ORIGIN` on MapTiler geocoding requests because the provider rejects origin-restricted requests with no identifying header. Provider failure preserves the form and does not affect liveness/readiness. Leaflet raster rendering uses MapTiler Streets v4; production builds fail when neither the override nor shared key is present, and the UI does not silently fall back to a questionable anonymous tile service. Caddy permits `api.maptiler.com` only in `img-src`; search/reverse-geocoding remain same-origin backend calls. Confirm provider terms, origin restrictions, attribution and quota before deployment; CivicAI claims no provider SLA.

## Rollback

Application/frontend rollback means checking out a previously verified commit, keeping `.env.production`, rebuilding, and starting again. Stop if the old code cannot operate against the current migration. Alembic downgrade is not automatic and destructive rollback is not assumed safe.

Restore a database only for actual data/schema recovery, not merely to roll back static assets. Use a verified pre-migration backup and the explicit restore process. This is a single-server restart deployment; it does not claim zero downtime or high availability.
