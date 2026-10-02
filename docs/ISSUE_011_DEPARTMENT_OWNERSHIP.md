# Issue #11 — Municipal departments, ownership, work queues and operational reliability

Status: **implemented, migrated and live-verified on 2026-10-02**.

Issue #7 Stage B remains paused. This issue changes only operational application code/data. It creates no research label, split, model, routing recommendation, priority or result.

## Bounded professional-system review

- OpenProject separates assignee/accountability, limits assignment to project members, retains activity history and provides filtered “assigned to me” work views. CivicAI adopts separate organizational ownership, individual responsibility, explicit membership and history; it does not add project hierarchy.
- GitLab documents issue assignees as visible accountability and boards as filtered views. CivicAI adopts canonical complaints with server-filtered queues and rejects a separate Kanban implementation for this milestone.
- Jira Service Management treats queues as filtered work-item views that respect permissions and expose summary/status/assignee. CivicAI adopts small, permission-aware queues and avoids custom query languages, SLA clocks and employee ranking.
- Sentry ownership rules map issues to teams/users. CivicAI retains that future extension point but rejects automatic rule/ML routing until a real routing contract and evidence exist.
- Stripe and AWS idempotency guidance informed retry handling. CivicAI uses naturally idempotent desired-state assignment commands plus optimistic concurrency instead of a generic retained idempotency-key store: an exact retry returns current state without another event; a different stale mutation returns 409.
- OWASP logging guidance informed separation of security events, business assignment history and local request logs. Request logs contain method, path, status, duration and a validated/generated request ID—not complaint text, coordinates, passwords, tokens or CSRF secrets.

Primary sources: [OpenProject work packages](https://www.openproject.org/docs/user-guide/work-packages/), [OpenProject members](https://www.openproject.org/docs/user-guide/members/), [GitLab issue assignees](https://docs.gitlab.com/user/project/issues/multiple_assignees_for_issues/), [GitLab issue boards](https://docs.gitlab.com/user/project/issue_board/), [Jira queues](https://support.atlassian.com/jira-service-management-cloud/docs/check-out-your-queues/), [AWS reliability idempotency](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_idempotent.html), [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests), [OWASP logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

## Relational model

- `municipal_departments`: UUID, immutable unique slug, normalized unique display-name key, display name, optional description, active flag and UTC timestamps. Names are NFKC/whitespace normalized and control characters rejected.
- `municipal_department_memberships`: many-to-many current relationship between a municipal user and department, including creator/time. Multiple membership supports cross-functional real operations without mixing organizational membership into authentication role.
- `department_membership_events`: immutable add/remove evidence. Current membership remains separate from historical facts.
- `complaints.department_id`: nullable current owning unit. Existing complaints migrate as organization-wide unassigned work.
- `complaints.assignee_user_id`: nullable individual responsibility. An assignee requires department ownership, an active account and current membership in that active department.
- `complaint_assignment_events`: immutable previous/resulting department and assignee IDs, actor, type, optional reason and UTC time. Foreign keys use `RESTRICT`; departments/users are deactivated, not deleted.

No department is auto-created. The administrator creates the small set of real municipal units in `/admin/departments`; demonstrations may use clearly named synthetic units.

## Permissions and queues

Administrators manage departments and membership, see all complaints and queues, and assign/reassign/unassign department/operator ownership. Operators see complaints belonging to any current department membership plus complaints still individually assigned to them, and may claim an unassigned complaint within a member department. Operators cannot manage departments, membership, cross-department ownership, or filter another operator's work.

Queues are server-paginated filters over canonical complaints:

- `unassigned`: no department; admin only;
- department queue: current member departments with no assignee;
- `mine`: assigned to authenticated user;
- all visible work: all complaints for admin, authorized department/individual work for operator.

Existing status/date/evidence/search filters compose with ownership filters. Generic text search does not join usernames or department names; ownership uses explicit IDs. Citizen list/detail schemas remain exactly operational-ownership-free.

## Assignment and lifecycle semantics

- Issue #8 status transitions remain unchanged. Assignment does not reset status.
- A complaint may be under review/in progress while unassigned because imposing a new assignment prerequisite would silently alter the verified lifecycle. The queue exposes that state for correction.
- Resolved/rejected complaints may retain or change ownership for truthful follow-up/reopening.
- Only administrators may unassign/reassign. An operator cannot abandon in-progress work through self-unassignment; an administrator must make that explicit change.
- Department reassignment clears no lifecycle data. If an assignee is supplied, they must belong to the resulting department.
- A successful self-claim uses one conditional update requiring the expected timestamp and still-unassigned state. Concurrent claim attempts therefore have one winner; the loser receives a stale conflict.

## Lifecycle safeguards

Departments are renamed by display name while stable IDs/slugs preserve links. They are deactivated rather than deleted. Deactivation is blocked while any unresolved complaint (`submitted`, `under_review`, `in_progress`) belongs to that department. New membership/assignment to an inactive department is blocked; resolved/rejected history remains visible. Reactivation is explicit.

Membership removal is blocked while that operator owns unresolved work in the department. Removal after resolved/rejected work is allowed without rewriting current/history records. Disabling an account preserves its current assignments and immutable history; the UI marks the assignee inactive and administrators must explicitly reassign. Reactivation restores access subject to live membership. No automatic redistribution occurs.

## Reliability

Current assignment and its event are committed in one SQLAlchemy/PostgreSQL transaction. A simulated history-constraint failure proves both roll back. `expected_updated_at` protects every ownership change. Exact same desired-state retries return the canonical complaint without changing `updated_at` or creating another event. A retry that represents a different desired state is not replayed blindly and fails stale.

Every response receives `X-Request-ID`. A caller-provided ID is accepted only when it matches 8–64 ASCII letters/digits/dot/underscore/hyphen; otherwise the server generates a 32-character UUID hex value. Local structured JSON request logs include request ID, method, path, response status and duration. This is correlation logging, not distributed tracing or production monitoring.

## UX and accessibility

The existing Issue #10 shell/design system is retained. Work-queue buttons expose pressed state; desktop uses ownership columns and narrow screens use the existing cards. Complaint detail shows current ownership, inactive state, assignment actions and history. Admin department management uses labeled native fields/buttons; self-claim requires no confirmation, while deactivation is a deliberate explicit action and backend safeguards provide actionable errors. No drag-and-drop is required.

## Future routing integration

Manual department/operator assignment is authoritative. A future service may separately return a recommended department, confidence, model version and explanation; accepting/overriding it should call the same assignment command and record the human actor. Issue #11 adds no placeholder prediction columns or category-to-department mapping.

## Limitations

- Request logs are local process logs with no retention/aggregation/monitoring system.
- Assignment idempotency is desired-state based; there is no long-lived cross-device idempotency-key result cache.
- No SLA, deadline, priority, notification, employee-performance score, board, bulk assignment, department hierarchy or multi-municipality tenancy exists.
- Public evidence access remains the existing local-prototype privacy limitation.
- Formal accessibility conformance and production-scale query/load testing are not claimed.

## Verification evidence

- Migration `0007` is the development PostgreSQL head. Direct database inspection confirmed the live synthetic complaint in `in_progress`, owned by the synthetic drainage department and operator, with two immutable assignment events and three status events.
- The real browser verified department creation, operator creation/membership, department assignment, operator queue visibility, self-claim, status progression and preserved-note stale-write rejection. The assigned queue and controls remained usable at a 390 × 844 CSS-pixel viewport. Reload after cleanup returned to sign-in, proving both temporary sessions were revoked; both temporary accounts were disabled. Browser warning/error logs were empty at the end of verification.
- The anonymous complaint response exposes no department, assignee or assignment-history field. A supplied safe request ID was returned unchanged by `/health`.
- Full regression passed: 177 Python tests (121 backend and 56 unchanged research), 27 citizen frontend tests, 23 municipal frontend tests, TypeScript compilation and the production build. The only warnings were the three previously recorded dependency deprecations (Starlette/httpx TestClient, AnyIO BlockingPortal alias and Alembic `path_separator`).
- The raw OpenCity file remained SHA-256 `d951dbb484532421801f6cbd7550edaa6f9ab143da7c4d0e835ba574e4e6d5ac`; Issue #7 Stage B remains paused and no research artifact or ML claim changed.
