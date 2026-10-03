# Operations runbook

## Fast status and diagnostics

```powershell
docker compose --env-file .env.production -f compose.production.yml ps
.\scripts\diagnose-production.ps1
```

The diagnostic command shows service health, migration head, a read-only evidence consistency report and the last 50 bounded log lines. It does not print environment variables or public disk metrics. Correlate a browser/API `X-Request-ID` with backend logs; request logs use normalized routes and exclude descriptions, coordinates, cookies, tokens, credentials and bodies.

## Site will not load

1. Check DNS and ports 80/443.
2. Check `proxy` health/logs and Caddy certificate messages.
3. Check that `frontend/dist` was created in the proxy build.
4. Check backend `/health` and `/ready` through the proxy.
5. Never bypass a TLS warning; fix DNS, time or certificate trust.

## API returns 502/503

Check `backend`, then `db`, then the `migrate` one-shot service. `/health` means the process is alive; `/ready` additionally requires PostgreSQL, migration `0007` and writable evidence storage. Readiness deliberately ignores the external geocoder. Fix the dependency and let Compose restart; do not create an infinite migration/retry loop.

## Login fails for everyone

Check HTTPS, host clock, `AUTH_ALLOWED_ORIGINS`, secure cookie attributes and PostgreSQL. Confirm the browser origin exactly matches the configured `https://` origin. Do not disable Secure cookies or CSRF to diagnose deployment. Use the interactive bootstrap command only if no viable administrator exists.

## Image is missing or access is denied

Unauthenticated image access should be 401; an authenticated operator without complaint access should be 403. For an authorized missing image, run `python -m civicai.media_audit` inside the backend, check the `evidence_data` mount/UID 10001 permissions and restore from the matching backup. Never make the evidence directory a public static mount.

## Database unavailable

Readiness returns sanitized 503 while liveness remains 200. Check volume capacity, container status and PostgreSQL logs. After recovery, SQLAlchemy's `pool_pre_ping` replaces stale pooled connections. Do not delete/recreate the volume as a troubleshooting shortcut.

## Disk nearly full

Inspect Docker disk usage and the host filesystems containing `postgres_data`, `evidence_data`, Caddy state and backups. Container JSON logs are limited to five 10 MiB files per service. Move verified old backups according to policy; do not delete live PostgreSQL/evidence files. External capacity alerting remains future deployment work.

## External map/geocoder unavailable

Citizen text/photo state remains in the form and the UI reports location lookup failure. The application stays live. Check provider quota/key/domain settings without logging the key. Do not promise provider availability or silently broaden country scope.

## Restart and recovery

Restart one component with:

```powershell
docker compose --env-file .env.production -f compose.production.yml restart backend
docker compose --env-file .env.production -f compose.production.yml restart proxy
```

PostgreSQL-backed sessions, complaint state, ownership/history and named-volume evidence survive application/proxy restart. A PostgreSQL restart causes temporary readiness failure and should recover; this is predictable recovery, not high availability.

## Security/incident notes

- Revoke/disable a municipal account through admin controls; sessions are server-side and revoked.
- Rotate a compromised database/provider credential in `.env.production`, then recreate affected services.
- Rotating `PUBLIC_TRACKING_SECRET` invalidates all existing private tracking links; record and communicate that consequence.
- Preserve relevant bounded logs/backups before repair. Never paste secrets, complaint text, coordinates or image bytes into an issue.
- Unexpected client errors must not expose stack traces. Use the response request ID to find server-side detail.

## Known operational limits

The design is single-host, with no automatic failover, centralized metrics, external log aggregation or distributed rate limiter. Login throttling remains process-local. Complaint submission, location lookup and evidence retrieval rely on validation, authorization and the 6 MiB proxy body cap but not a distributed abuse-control service. Add provider/host-specific rate controls only after measuring normal municipal use; do not lock operators out with guessed thresholds.
