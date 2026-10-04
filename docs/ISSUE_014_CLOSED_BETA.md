# Issue #14 — Zero-cost closed beta

Status: deployment preparation implemented and locally verified; external provisioning and live verification are pending. This is not production certification.

Local Phase A gates: 147 backend tests and 56 unchanged research tests passed (203 total), 57 frontend tests passed, TypeScript compilation and the beta-configured Vite production build passed, `pip check` and `git diff --check` passed. The raw OpenCity checksum was reverified as `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. The Dockerfile could not be executed from the Codex sandbox because access to the local Docker named pipe was denied; GitHub CI now builds this image and the Render deployment will provide the next runtime proof.

## Architecture

The beta uses one Render Free web service and one public HTTPS origin. `Dockerfile.beta` builds React, then runs FastAPI/Uvicorn, applies Alembic migrations before startup, serves the built SPA (including deep-link fallback), and keeps `/api/*`, `/health`, and `/ready` as API routes. The existing local Docker/Caddy/PostgreSQL/Mailpit system is unchanged.

Supabase is infrastructure only: hosted PostgreSQL plus a private Storage bucket accessed through its server-side S3-compatible API. CivicAI remains the authorization boundary. Evidence is sanitized before upload, stored under an opaque UUID key, and streamed only through the existing authenticated complaint-image endpoint. Supabase credentials and object URLs never enter browser bundles.

Brevo sends verification, reset, and staff-invitation messages through its HTTPS transactional API. Capture/SMTP remain available locally. Beta/production reject capture and disabled email modes.

## Free-tier constraints verified from official documentation

- Render Free web services [spin down after 15 minutes idle](https://render.com/docs/free), have an ephemeral filesystem, and do not provide persistent disks or dashboard shell access. Cold starts are expected. Render blocks outbound SMTP ports, so the beta uses an HTTPS email API.
- Render currently offers Singapore, the closest listed region to India. Supabase offers Mumbai (`ap-south-1`). This deliberately accepts cross-region application/database traffic in exchange for placing the database and evidence nearer beta users.
- Supabase Free currently includes a 500 MB database and 1 GB Storage allowance. Low-activity free projects may pause. The application uses the IPv4-compatible shared pooler in session mode and a deliberately small SQLAlchemy pool.
- Brevo Free currently allows 300 email sends/day. A sender must be verified, and free-plan branding may remain.

## Configuration and security

Use `.env.beta.example` only as a variable-name guide. Never commit a populated beta environment file. Render secrets include the database URL/password, tracking secret, Supabase S3 credentials, Brevo key, backend MapTiler key, and Google client secret. `VITE_MAPTILER_API_KEY` is public by design and must be origin-restricted at MapTiler.

`render.yaml` declares a free Singapore Docker service, `/ready` health check, and deployment only after GitHub checks pass. The generated Render hostname must replace all example host values before deployment. Migrations run before each process start and fail the deployment if they fail.

## Backup and recovery limits

Supabase recommends that Free projects make regular off-site CLI database dumps. Database backups do not include Storage objects; evidence requires a separate export. The beta has no formal recovery-time guarantee. Before a destructive change, export both PostgreSQL and the private bucket and verify the exports can be read.

## Sources

- [Render Free](https://render.com/docs/free), [Docker](https://render.com/docs/docker), [health checks](https://render.com/docs/health-checks), [Blueprint specification](https://render.com/docs/blueprint-spec)
- [Supabase database connections](https://supabase.com/docs/guides/database/connecting-to-postgres), [pooling](https://supabase.com/docs/guides/database/connecting-to-postgres/pooling-and-limits), [private buckets](https://supabase.com/docs/guides/storage/buckets/fundamentals), [S3 authentication](https://supabase.com/docs/guides/storage/s3/authentication), [backups](https://supabase.com/docs/guides/platform/backups)
- [Brevo transactional email API](https://developers.brevo.com/reference/send-transac-email), [Free plan limits](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan), [sender setup](https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email)
- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
