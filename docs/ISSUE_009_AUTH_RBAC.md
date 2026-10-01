# Issue #9 — Municipal Authentication and Role-Based Access Control

Status: implemented and locally verified on 2026-10-01.

## Scope and result

Issue #9 protects the existing municipal operations surface without changing the anonymous citizen workflow or resuming research/ML. It adds PostgreSQL municipal users, opaque server sessions, Argon2id passwords, login/logout/session recovery, server-enforced operator/admin roles, a minimal administrator account page, CSRF protection, login throttling, security audit events and authenticated complaint-history actor attribution.

It deliberately does not add citizen accounts, public registration, OAuth/social login, email/password reset, MFA, SSO, departments, tenancy, routing, notifications, ML or deployment infrastructure.

## Security guidance consulted

- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): selected Argon2id and its minimum `m=19456 KiB`, `t=2`, `p=1` profile.
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html): opaque unpredictable session identifiers, HttpOnly/Secure/SameSite cookie controls, expiry and server-side invalidation.
- [OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): session-bound token plus SameSite and Origin validation as layered defenses.
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html): generic authentication failures and abuse throttling without permanent account lockout.
- [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html) and [OWASP HTML5 Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html): backend authorization and deliberate same-origin/CORS handling.
- [MDN Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie): cookie attribute and expiry behavior.

No tutorial or comparable product was treated as a security authority.

## Authentication architecture

The browser receives 256 bits of random session material in a host-only, path `/`, HttpOnly, SameSite=Strict cookie. PostgreSQL stores only SHA-256 of that token, not the raw credential. `municipal_sessions` also stores the owning user, creation/expiry/revocation time and a separate random CSRF secret. `/auth/me` returns safe user fields, expiry and that CSRF value; the frontend keeps it in React memory only. Authenticated mutations send it as `X-CSRF-Token`. When Origin is present it must exactly match the configured local origins.

The timeout is absolute, eight hours by default and configurable from one to 24 hours. Expiry/revocation returns 401; frontend startup and refresh always call `/auth/me`. Logout revokes the database row before deleting the cookie. Disabling an account revokes its sessions, while every request also reloads the active user and current role.

No signing secret is required because sessions are opaque and database-backed. `APP_ENV=production` refuses to start unless `AUTH_COOKIE_SECURE=true`. Local HTTP keeps Secure false. No CORS middleware is enabled: supported local browser requests are same-origin through Vite; production assumes a same-origin reverse proxy. A future separate frontend origin needs explicit credentialed-CORS design, never wildcard origin.

## Roles and account constraints

- `municipal_operator`: dashboard, complaint list/search/filter/detail/history/evidence and allowed status/note mutation.
- `municipal_admin`: all operator rights plus municipal account list/create/disable/reactivate/role assignment.

Every admin route checks the database role server-side. Operators cannot invoke account APIs even by calling them directly. Username is normalized lowercase, unique and restricted to a small safe character set. Account schemas never contain password hashes. Duplicate/invalid accounts fail cleanly. The current admin cannot disable or demote itself; the final active admin cannot be disabled or demoted. There is no delete-account endpoint.

The first admin is created only with `python -m civicai.bootstrap_admin`. It reads password and confirmation with `getpass`, hashes before persistence, refuses an existing active admin and prints no secret. There are no default credentials or registration endpoint.

## Abuse, audit and data boundaries

Wrong password, missing username and disabled account produce the same login response. A bounded process-local sliding window limits five failures per ten minutes independently by IP and normalized username. This is defensible for the single-process academic demo; multi-instance deployment requires shared proxy/datastore throttling.

`security_audit_events` records account created/disabled/reactivated, role change, successful login and logout with actor/subject UUIDs and time. It stores no password, raw token, CSRF value or failed-password data. Complaint status history remains a separate immutable table. Migration `0006` adds a nullable foreign key from its actor to municipal users; old null events remain unchanged and all new authenticated changes record the actor.

Citizen complaint list/detail responses continue using `ComplaintRead`, which contains neither history nor operator notes. Municipal schemas are separate. Account and session tables are never exposed to citizen routes. Public evidence URLs remain a documented local-prototype privacy limitation and are not presented as production-ready access control.

## Verification

- Alembic `0006` applied successfully to the disposable test schema and development PostgreSQL.
- 166 Python tests passed: 110 backend and 56 unchanged research.
- 39 frontend tests passed: 24 citizen and 15 municipal/authentication.
- The combined frontend launch hit the known Windows worker-start timeout after the citizen file passed; the municipal file then passed in its conclusive isolated run.
- TypeScript compilation and production build passed.
- Raw OpenCity CSV SHA-256 remained `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`.
- Real browser/PostgreSQL flow verified unauthenticated blocking, generic invalid login, admin/operator login, refresh, role-restricted navigation, authenticated status mutation, actor/note persistence, account creation, operator 403, disable/session rejection/reactivation, logout invalidation and anonymous citizen access.
- Browser warning/error log was empty.
- Both `issue9.demo.*` verification accounts were disabled and all their sessions revoked afterward; their rows remain only to preserve truthful audit/history foreign keys. The project owner can now bootstrap a private administrator.

The live browser exposed a timezone defect not visible in the UTC test schema: PostgreSQL returned expiry with `+05:30`, while cookie formatting required a UTC datetime. Login now converts expiry to UTC and a regression test covers the non-UTC value.

## Known limitations

- The login throttle is process-local and resets with the backend; production needs shared rate limiting and monitoring.
- Sessions use absolute rather than idle expiry; administrators cannot view/revoke individual sessions yet.
- No password change/reset/recovery or MFA exists. Admins must create a replacement account through an operational process.
- HTTPS, reverse-proxy hardening, secret rotation policy, backups, audit retention and production evidence access remain deployment work.
- Security audit events have no administrator UI in this issue.
- Public citizen complaint and evidence access remains suitable only for synthetic/local demonstrations.

## Completion boundary

Issue #7 Stage B remains paused. No research record, review form, raw source, taxonomy, label, split or model was modified. No research result or unsupported novelty claim is made.
