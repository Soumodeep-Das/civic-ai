# Issue #13 — Modern identity, citizen accounts and municipal staff access

Status: implemented; automated and production-like browser verification complete.

## Identity architecture

CivicAI separates identity populations. `citizen_accounts` contains self-service citizen identity/profile state; password hashes live in `citizen_password_credentials`; Google identities are keyed by immutable `(provider, issuer, subject)` in `federated_identities`. Existing `municipal_users` remain the sole municipal authorization relationship and retain role, active state, department membership and historical foreign keys. Matching a citizen email never creates municipal authority.

`municipal_sessions` is evolved into the shared opaque session store. Each row has exactly one principal: a municipal user or a citizen account. Existing staff rows remain valid because their `user_id` values are preserved. Browser cookies contain random material; PostgreSQL stores only SHA-256 digests.

This conservative design avoids a destructive rewrite of proven Issue #9/#11 identities. A person who is both citizen and staff presently has two explicit identities; CivicAI never links or elevates them from an email match.

## Citizen flows

- Anonymous reporting and Issue #12 private capability links remain supported.
- Email/password signup creates `pending_verification`; a hashed, single-use, one-hour token activates the account.
- Citizen passwords require 15–128 characters, accept spaces/paste, impose no composition/rotation rule, use Argon2id and reject a bounded set of extremely common/context-specific values.
- Email normalization trims whitespace and lowercases the complete address for comparison. It does not remove dots, aliases or apply provider-specific rewriting. PostgreSQL enforces uniqueness.
- Sign-in is generic on failure and process-locally throttled. Disabled and unverified accounts cannot sign in.
- Forgot-password responses are generic. Hashed 30-minute reset tokens are single-use; successful reset revokes every citizen session and does not automatically sign in.
- Authenticated password change requires the current password and revokes other sessions.
- Authenticated complaint submission derives ownership only from the server session. `/my-complaints` and detail queries are account-scoped in SQL. Citizen history exposes public status/time, never actor, internal note, assignment or security events.
- A verified citizen may claim an older anonymous complaint only with its valid private tracking capability. Claim is idempotent for the same account and conflicts for a different owner.
- Profile reports verification, password availability and Google connection state. Account deletion and a set-password flow for Google-only accounts are deferred.

## Google OpenID Connect

CivicAI uses Google's documented server-side authorization-code flow. A ten-minute database flow stores hashed state/nonce; temporary HttpOnly SameSite=Lax cookies bind the cross-site callback without weakening the primary SameSite=Strict session. The backend exchanges the code over TLS, verifies the ID-token RS256 signature with Google's discovered JWKS through `joserfc`, and validates issuer, client audience, expiry, nonce, subject, email and `email_verified=true`.

New Google identities create citizen accounts only. CivicAI stores issuer+subject and no Google access/refresh token. An existing password account with the same normalized email is refused; unsafe email-only auto-linking is impossible. Explicit linking and municipal Google sign-in are deferred.

Configure a Google OAuth web client with callback `/api/v1/citizen-auth/google/callback`. Use the exact local served origin/redirect for development and the real HTTPS CivicAI domain in deployment. Consent-screen test users may be required while the Google project is in testing. Real credentials stay only in ignored environment files.

## Email delivery

`EmailService` provides ignored-file capture for development, configurable STARTTLS SMTP for production, and an explicit disabled adapter. Development capture writes tokens under ignored `tmp/dev-mail`, never ordinary request logs. Tests override capture to isolated per-test temporary directories so synthetic tokens cannot pollute the developer inbox. Production rejects capture mode. Verification, reset and invitation tokens are not returned by APIs or stored raw in PostgreSQL.

The optional `compose.production.mailpit.yml` override supports local production-like SMTP verification. It binds Mailpit's web inbox only to host loopback on port 8025, leaves SMTP private to the Compose network and overrides the backend transport to unencrypted SMTP within that private local network. The normal production Compose file contains no Mailpit service and retains fail-closed email configuration; this override must never be used for a real deployment.

## Municipal access

The first administrator remains an operational `python -m civicai.bootstrap_admin` action. Existing username/password login remains compatible at visible `/staff/sign-in`. The primary workspace is `/municipal`; old `/admin` bookmarks are accepted and subsequent navigation uses role-neutral paths.

Administrators invite staff by email, fixed role and fixed active departments. A hashed, single-use, 72-hour invitation lets the recipient choose display name, username and password, never role/membership. Expired, revoked, used or operationally invalid invitations cannot activate an account. The inviter must remain active and selected departments active. Direct account creation remains as a protected backward-compatible API for existing operational/tests, but is not public and the UI uses invitations.

## Authorization invariants

- Public signup and Google sign-in produce citizens only.
- No unauthenticated API selects staff role or department membership.
- Citizen sessions fail municipal dependencies; municipal sessions fail citizen dependencies.
- Municipal role/membership remain server-enforced; final-admin/self-demotion safeguards remain.
- Complaint ownership comes from the validated session, never a browser account ID.
- Evidence is available only to authorized municipal staff or the owning citizen.
- Cookie-authenticated mutations require session CSRF and an allowed Origin.

## Research basis

Adopted patterns came from current [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/), OWASP Authentication, Session Management, Forgot Password, Email Validation/Verification and OAuth guidance, and [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect). Adopted: long passwords without composition rules, bounded blocklist/throttling, generic recovery, hashed single-use tokens, opaque revocable sessions, state/nonce, verified JWT claims and issuer+subject keys. Rejected: JWT/localStorage sessions, implicit flow, email-only federation linking, public role selection, permanent temporary passwords, provider-specific email rewriting and broad CSP relaxation.

## Migration and compatibility

Alembic `0008` adds citizen accounts/credentials, federated identities, identity tokens, OIDC flows, staff invitations/grants, citizen complaint ownership, citizen audit references and citizen principals on the existing session table. An exclusive-principal check protects sessions. Existing migrations are unchanged. Upgrade from `0007` and fresh-to-head are exercised by the migration/model suite.

## Verification

- Backend: 143 tests passed in one conclusive full-suite run.
- Research: 56 unchanged tests passed.
- Frontend: 57 tests passed in one conclusive single-worker run; TypeScript and the Vite production build passed.
- Three pre-existing deprecations remain: Starlette/httpx TestClient, AnyIO BlockingPortal alias and Alembic `path_separator`.
- The owner verified real Google authorization, callback to My Complaints, the normal CivicAI server-side session, refresh persistence, Google-connected profile state and logout through `https://localhost`. Deterministic tests additionally cover new identity creation, safe email collision and invalid issuer/audience/expiry/nonce. No municipal authority is inferred from Google identity.
- A browser callback carrying provider cancellation was redirected to `/sign-in?google_error=cancelled` and rendered only the generic recovery message; no provider detail, code or token was exposed.
- The owner verified a production-like municipal invitation from creation through Mailpit delivery and successful account activation. An initial 400 exposed cross-environment synthetic test mail in the development inbox; tests now use isolated temporary inboxes, and a 14-test identity rerun proved the developer inbox count does not change.
- The invited operator then signed in through `/staff/sign-in`, reached the authorized dashboard/complaint queue, saw no Municipal Staff or Departments controls, received the administrator-permission denial at the direct `/municipal/users` route and successfully signed out.
- The normal production Compose remains free of a debug inbox. The local Mailpit override is explicit, loopback-only on its web port and documented as prohibited for real deployment.

## Limitations

- Sensitive-endpoint throttles are process-local; multi-instance deployment needs shared enforcement.
- SMTP is synchronous and suitable for this single-server project; a durable job queue is future scaling work.
- Explicit Google linking/unlinking, staff Google login, invitation resend, citizen account deletion, MFA/passkeys and notifications are deferred.
- Email deliverability, domain reputation and consent-screen approval depend on providers.
- This is MCA product security hardening, not formal certification or penetration testing.

Issue #7 Stage B remains paused. No research source, label, taxonomy, model or claimed result changed.
