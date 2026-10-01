# Issue #10 — Professional UX, responsive design, accessibility and performance hardening

Status: **completed and live-verified locally on 2026-10-02**.

Issue #10 improves the existing citizen and authenticated municipal experiences without changing complaint, lifecycle, authentication, RBAC, CSRF, evidence or research contracts. It does not add ML, routing, citizen accounts, notifications or a database migration. Issue #7 Stage B remains paused.

## Pre-implementation audit

The audit combined source/test inspection with the running development application in the in-app Chromium browser. The existing product has strong foundations: semantic form labels and fieldsets, plain-language citizen copy, preserved inputs after request failures, duplicate-submit disabling, explicit loading/empty/error states, credential autocomplete, role-aware navigation, lazy map loading, textual location alternatives, truthful status labels and reduced-motion CSS.

Meaningful gaps found before visual changes:

- The citizen and municipal experiences shared one eager JavaScript entry, so citizen visitors downloaded all municipal code.
- Every non-admin unknown path rendered the citizen home, and unknown `/admin/*` paths rendered the dashboard. There was no frontend 404.
- The page title was the same on all routes.
- Repeated headers had no skip link. The citizen header was not a navigation landmark.
- Citizen submit validation kept keyboard focus on the Submit button. There was no focusable linked error summary, and the location combobox was not programmatically associated with the location error.
- Selected photos had a filename but no preview. Complaint-list evidence had no broken-image fallback or reserved aspect ratio.
- Citizen success feedback gave only a shortened reference and did not state current status, what happens next or a clear next action.
- The citizen form preserved current React state after API/geocoder failures, but had no warning against accidental refresh/navigation. Persisting precise location or photo data was rejected on privacy grounds.
- The municipal mobile header occupied about 214 px at the narrow test viewport.
- At a browser-reported 356 px viewport, the complaint-list route expanded the document to about 910 px because the desktop table remained the only representation. Users had to pan a data table horizontally.
- Municipal filters had no active-filter summary and the empty copy did not distinguish an empty system from zero filtered results.
- Session expiry returned to login without explaining why.
- Status conflicts surfaced backend wording but did not provide a dedicated, action-oriented recovery state.
- Rejecting a complaint, changing an account role and disabling an account had no consequence confirmation.
- Unknown/malformed complaint routes had no route-level recovery page.
- Municipal evidence images were eager and had no intrinsic/aspect-ratio reservation. Citizen evidence was lazy but likewise had no reserved ratio.
- Controls had inconsistent focus styling, several small targets, and some subdued text/borders needed stronger contrast. The visual language used many one-off values instead of documented tokens.
- The existing production build was one 259.24 kB JavaScript entry (79.01 kB gzip) plus a 150.70 kB lazy map chunk (44.24 kB gzip). This is the before-change lab bundle baseline, not field performance.

The desktop citizen layout did not horizontally overflow at the tested default browser size, and the narrow citizen form remained within the viewport. Login credential labels/autocomplete, detail single-column reflow and map text fallbacks were already sound. Existing behavior is retained unless a finding above justifies a change.

## Authoritative guidance reviewed

- [GIGW 3.0](https://guidelines.india.gov.in/) emphasizes citizen-focused, user-friendly Indian public sites, semantic markup, accessible forms, mobile friendliness, assistive-technology support and meaningful non-text alternatives. CivicAI adopts these as design constraints but does not claim GIGW certification or government status.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) informs reflow around 320 CSS pixels, keyboard operation, bypass blocks, page titles, visible/unobscured focus, textual error identification, status messages and the 24-by-24 CSS-pixel minimum target criterion. CivicAI generally aims for roughly 44 px controls where space allows. This issue is a practical AA-oriented hardening effort, not a conformance certification.
- [GOV.UK error-summary guidance](https://design-system.service.gov.uk/components/error-summary/) requires a summary plus matching inline messages, links to erroneous fields and focus movement to the summary. CivicAI adopts that pattern for complaint submission.
- [GOV.UK responsive-layout guidance](https://design-system.service.gov.uk/styles/layout/) starts with a single column on small screens and limits desktop line length. CivicAI adopts content-width limits and space-driven breakpoints rather than named-device layouts.
- [USWDS form guidance](https://designsystem.digital.gov/components/form/) supports vertical form order, fieldset/legend relationships and validation aligned with inputs. CivicAI retains semantic HTML and avoids a large component-framework dependency.
- [USWDS accessibility guidance](https://designsystem.digital.gov/documentation/accessibility/) explicitly treats component accessibility as a foundation that still requires page-level manual testing. CivicAI therefore combines tests, DOM inspection and keyboard/browser checks and makes no automated-tool-only claim.
- [web.dev code-splitting guidance](https://web.dev/articles/code-splitting-suspense) recommends route-level splitting as a simple first boundary. CivicAI will lazy-load the municipal application and keep the map interaction lazy.
- [web.dev image lazy-loading guidance](https://web.dev/articles/browser-level-image-lazy-loading) recommends native lazy loading and reserving image dimensions/aspect ratio to reduce layout shift. CivicAI will preserve original evidence bytes and optimize display only.
- [web.dev Core Web Vitals thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds) defines good field targets of LCP at or below 2.5 s, INP at or below 200 ms and CLS at or below 0.1 at the 75th percentile. Local build/browser evidence in this issue is reported only as lab evidence.

## Adopted product principles

1. Keep the primary citizen task linear on one page: describe, add evidence, choose/confirm location, submit.
2. Use plain language, preserve valid work after recoverable failures and provide a focused error summary after validation.
3. Keep precise location and photo ephemeral in the browser; warn about leaving a meaningful unfinished report rather than persisting those values.
4. Use a small token-based design system and native semantic controls. Add no UI framework.
5. Start layouts as one column, enhance at available-width breakpoints and provide mobile municipal cards instead of shrinking the desktop table.
6. Never use color as the sole status signal; pair a text label with a small decorative status marker.
7. Confirm only consequential municipal actions to avoid confirmation fatigue.
8. Retain useful loaded content during scoped errors where possible and offer a meaningful retry or refresh action.
9. Split municipal and map code from the citizen entry and reserve media/map space without altering original evidence.
10. Treat PWA/offline installation as future work: responsive reliability has higher value and a service worker would expand cache/security/update scope.

## Implemented design and interaction changes

- Formalized a compact CSS token system for type, spacing, content width, surfaces, borders, radii, shadows, semantic feedback, statuses and focus. System fonts replace the external font request; no frontend dependency was added.
- Kept citizen reporting on one page with four explicit sections, clearer evidence/privacy language, photo preview/removal, confirmed-location context and a complete success panel containing the canonical reference, current status, next-step explanation and report-another action.
- Added a focusable error summary linked to each invalid field while retaining matching inline errors and valid input. The location combobox now exposes its invalid state and related hint/error text programmatically.
- Added an accidental-navigation warning only while a meaningful unsent draft exists. Description, photo bytes and precise location are not written to browser storage and are cleared after acknowledged submission.
- Added skip links, semantic navigation/landmarks, route-specific document titles, visible focus treatment, comfortable controls, text-plus-colour status badges, polite dynamic feedback and reduced-motion handling.
- Added real citizen and municipal 404 routes instead of silently rendering an unrelated page.
- Reworked the municipal shell for a compact mobile menu with `aria-expanded`, first-link focus, outside/Escape close and focus restoration. The complaint table becomes task-focused cards below the table breakpoint while search, filters, result count, pagination, status, identity and primary actions remain available.
- Distinguished empty queues, zero filtered results and failed loads. Added active-filter feedback, scoped retries, explicit session-expiry copy, dedicated stale-update guidance that preserves the operator note, and confirmation dialogs only for rejection, role change and account disable.
- The accessible confirmation dialog moves focus inside, traps Tab, supports Escape/cancel and returns focus to the initiating control.
- Evidence uses contextual alternative text, native lazy loading, intrinsic dimensions/aspect-ratio reservation and a broken-image fallback. Textual location remains available if the map cannot render.

## Responsive strategy

Layouts start as a single readable column and switch based on available content width at `48rem` and `68rem`; there are small-width and narrow-landscape refinements without named-device assumptions. The citizen form and municipal cards wrap references, locations, badges and actions instead of widening the page. At wider widths, the citizen form/status list and complaint detail use bounded columns, and the admin table/navigation return. Maps remain two-dimensional controls but never replace the textual location.

## Performance evidence

Route-level `React.lazy`/`Suspense` separates municipal code from the citizen entry while preserving the already lazy map boundary. Native lazy evidence images reserve their display box, and the stylesheet no longer performs a render-blocking external font import. The production build changed from a 259.24 kB initial JS entry (79.01 kB gzip) to a 246.02 kB entry (76.31 kB gzip), plus a 30.07 kB lazy municipal chunk (7.86 kB gzip) and the unchanged 150.70 kB lazy map chunk (44.24 kB gzip). These are local build sizes, not field Core Web Vitals.

## Verification completed

- Citizen component suite: **27 passed**.
- Municipal component suite: **20 passed**. The suites were run as isolated single-worker files because the documented Windows worker-start issue can affect a combined Vitest launch.
- Backend/research regression: **166 passed** (110 backend and 56 unchanged research), with only the three previously recorded dependency deprecations.
- TypeScript project compilation and Vite production build: passed using repository-local executables because the host's global `npm` launcher remains broken.
- Real Chromium browser checks covered browser-reported widths of approximately 356, 400, 434, 478, 822/853, 1,138, 1,422 and 1,600 px, including a narrow landscape layout. Citizen and municipal routes showed no horizontal page overflow; small widths used municipal cards/menu and wide widths used the table/full navigation.
- Keyboard/semantic checks confirmed error-summary focus and field links, programmatic field errors, menu open/Escape/focus restoration, confirmation cancel/focus restoration, landmarks, route titles and genuine citizen/admin 404 pages.
- A synthetic narrow-screen report with a project-local PNG and searched Kolkata location was acknowledged as `731ddc82-b3d4-4ffa-82b7-5ee381d30273`, appeared in the municipal card queue with photo/location, rendered evidence and map, and advanced from Submitted to Under review with an internal audited note. Logout succeeded. The temporary audit administrator was then disabled and its sessions revoked.
- Console errors recorded during source hot-reload were timestamped before the verification run; no new warning/error was produced by the completed flow.
- The raw OpenCity CSV remains SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`. No research file, decision, label, split, taxonomy or approval changed.

## Known baseline limitations

The in-app browser is Chromium-based; a materially different engine is not currently connected. The responsive override reports scaled effective widths on this Windows host, so the evidence records the browser-reported widths rather than claiming exact device emulation. Automated/component checks cannot establish GIGW or WCAG conformance, and no screen-reader user study, formal contrast audit, low-end physical-device study or field Core Web Vitals dataset exists. Public geocoding/tiles remain best-effort local-demo services, and public evidence access remains an existing prototype privacy limitation. Full offline/PWA support remains deliberately out of scope.

## Exactly one recommended next issue

**Issue #11 — Deployment and operational readiness.** Define a supported production topology and harden configuration, reverse-proxy HTTPS/cookie handling, evidence access, backups/restores, structured logging, health/diagnostics, secrets, retention and deployment verification before any public pilot. Do not resume Issue #7 Stage B or ML work until real human reviewers complete its documented gates.

## Git publication status

The verified working tree is based on synchronized `main` commit `6ce0f17`, and GitHub `main` still pointed to that commit at the completion check. This Codex sandbox could not create `.git/index.lock` because an OS-level deny ACL remained in force even after narrowly scoped repository-metadata permission was granted. A side-effect-free alternate object-store commit was prepared, but the sandboxed Git credential helper could not authorize the push. No remote history changed. The owner must run the documented `git add`, `git commit` and `git push` commands from their normal PowerShell identity.
