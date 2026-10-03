import { AriaAttributes, FormEvent, ReactNode, Suspense, lazy, useCallback, useEffect, useRef, useState } from "react";

import {
  AdminComplaint, AdminComplaintPage, ApiError, ComplaintStatus, DashboardStatistics,
  claimComplaint, getAdminComplaint, getDashboardStatistics, getWorkQueueStatistics, imageUrl, listAdminComplaints,
  updateComplaintAssignment, updateComplaintStatus,
} from "../api/complaints";
import {
  AuthSession, MunicipalDepartment, MunicipalRole, MunicipalUser, StaffInvitation, addDepartmentMember,
  createDepartment, getSession, listDepartments, listUsers, login, logout,
  removeDepartmentMember, updateDepartment, updateUser, inviteStaff, listStaffInvitations, revokeStaffInvitation,
} from "../api/auth";
import { ConfirmDialog } from "../ui/ConfirmDialog";
import { StatusBadge, statusLabels } from "../ui/StatusBadge";

const ReadOnlyLocationMap = lazy(() => import("../LocationMap"));

const roleLabels: Record<MunicipalRole, string> = {
  municipal_operator: "Municipal operator",
  municipal_admin: "Municipal administrator",
};

const allowedTransitions: Record<ComplaintStatus, ComplaintStatus[]> = {
  submitted: ["under_review", "rejected"], under_review: ["in_progress", "rejected"],
  in_progress: ["under_review", "resolved", "rejected"], resolved: ["under_review"], rejected: ["under_review"],
};

function readableDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function useDocumentTitle(title: string) { useEffect(() => { document.title = title; }, [title]); }

function usePathname() {
  const normalize = (value: string) => {
    const clean = value.replace(/\/$/, "") || "/";
    if (clean === "/staff/sign-in") return "/admin/login";
    return clean.replace(/^\/municipal/, "/admin");
  };
  const publicPath = (value: string) => value.replace(/^\/admin/, "/municipal");
  const [path, setPath] = useState(normalize(window.location.pathname));
  useEffect(() => {
    const change = () => setPath(normalize(window.location.pathname));
    window.addEventListener("popstate", change); return () => window.removeEventListener("popstate", change);
  }, []);
  const navigate = useCallback((next: string) => {
    const visible = next === "/admin/login" ? "/staff/sign-in" : publicPath(next);
    window.history.pushState({}, "", visible); setPath(normalize(visible)); window.scrollTo({ top: 0 });
  }, []);
  return [path, navigate] as const;
}

function AdminLink({ href, children, className, navigate, onNavigate, ...aria }: { href: string; children: ReactNode; className?: string; navigate: (path: string) => void; onNavigate?: () => void } & AriaAttributes) {
  return <a href={href} className={className} {...aria} onClick={(event) => {
    if (event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) { event.preventDefault(); navigate(href); onNavigate?.(); }
  }}>{children}</a>;
}

function LoginPage({ returnTo, message, onAuthenticated }: { returnTo: string; message?: string; onAuthenticated: (session: AuthSession, path: string) => void }) {
  useDocumentTitle("Municipal sign in | CivicAI");
  const [username, setUsername] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [submitting, setSubmitting] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (submitting) return; setSubmitting(true); setError("");
    try { onAuthenticated(await login(username, password), returnTo); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Sign in failed. Check your details and try again."); }
    finally { setSubmitting(false); }
  }
  return <main className="admin-login-page" id="main-content"><section className="admin-login-card" aria-labelledby="login-title">
    <a href="/" className="admin-brand">Civic<span>AI</span> Operations</a>
    <p className="eyebrow">Restricted municipal workspace</p><h1 id="login-title">Municipal staff sign in</h1>
    <p>Use your approved staff account. Need municipal access? Contact your municipal administrator.</p>
    {message && <div className="admin-notice" role="status">{message}</div>}
    {error && <div className="admin-state admin-error" role="alert"><strong>Sign in failed</strong><p>{error}</p></div>}
    <form onSubmit={submit}><label htmlFor="admin-username">Username</label><input id="admin-username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /><label htmlFor="admin-password">Password</label><input id="admin-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /><button type="submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button><span className="sr-only" role="status">{submitting ? "Signing in. Please wait." : ""}</span></form>
    <a href="/">Return to citizen portal</a>
  </section></main>;
}

function AdminShell({ children, path, navigate, session, onLogout }: { children: ReactNode; path: string; navigate: (path: string) => void; session: AuthSession; onLogout: () => Promise<void> }) {
  const [menuOpen, setMenuOpen] = useState(false); const menuButton = useRef<HTMLButtonElement>(null); const nav = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!menuOpen) return;
    nav.current?.querySelector<HTMLElement>("a")?.focus();
    const close = (event: KeyboardEvent | MouseEvent) => {
      if (event instanceof KeyboardEvent && event.key === "Escape") { setMenuOpen(false); menuButton.current?.focus(); }
      else if (event instanceof MouseEvent && !nav.current?.contains(event.target as Node) && !menuButton.current?.contains(event.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("keydown", close); document.addEventListener("mousedown", close);
    return () => { document.removeEventListener("keydown", close); document.removeEventListener("mousedown", close); };
  }, [menuOpen]);
  const closeMenu = () => setMenuOpen(false);
  return <div className="admin-app"><a className="skip-link" href="#main-content">Skip to main content</a><header className="admin-header">
    <AdminLink href="/admin" navigate={navigate} className="admin-brand">Civic<span>AI</span> Operations</AdminLink>
    <button ref={menuButton} className="admin-menu-button" type="button" aria-expanded={menuOpen} aria-controls="admin-navigation" onClick={() => setMenuOpen((value) => !value)}><span aria-hidden="true">☰</span> Menu</button>
    <nav ref={nav} id="admin-navigation" className={menuOpen ? "open" : ""} aria-label="Municipal navigation">
      <AdminLink href="/admin" navigate={navigate} onNavigate={closeMenu} className={path === "/admin" ? "active" : undefined}>Dashboard</AdminLink>
      <AdminLink href="/admin/complaints" navigate={navigate} onNavigate={closeMenu} className={path.startsWith("/admin/complaints") ? "active" : undefined}>Complaints</AdminLink>
      {session.user.role === "municipal_admin" && <AdminLink href="/admin/users" navigate={navigate} onNavigate={closeMenu} className={path === "/admin/users" ? "active" : undefined}>Municipal Staff</AdminLink>}
      {session.user.role === "municipal_admin" && <AdminLink href="/admin/departments" navigate={navigate} onNavigate={closeMenu} className={path === "/admin/departments" ? "active" : undefined}>Departments</AdminLink>}
      <a href="/">Citizen view</a>
    </nav>
    <div className="admin-identity"><span>{session.user.username}<small>{roleLabels[session.user.role]}</small></span><button type="button" onClick={() => void onLogout()}>Sign out</button></div>
  </header><main id="main-content" tabIndex={-1}>{children}</main><footer><span>CivicAI municipal operations</span><span>Authenticated operational data · no ML predictions</span></footer></div>;
}

function Dashboard({ navigate, onExpired, session }: { navigate: (path: string) => void; onExpired: () => void; session: AuthSession }) {
  useDocumentTitle("Operations dashboard | CivicAI");
  const [stats, setStats] = useState<DashboardStatistics>(); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const [work, setWork] = useState<Awaited<ReturnType<typeof getWorkQueueStatistics>>>();
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const [totals, queues] = await Promise.all([getDashboardStatistics(), getWorkQueueStatistics()]); setStats(totals); setWork(queues); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Dashboard statistics could not be loaded."); }
    finally { setLoading(false); }
  }, [onExpired]);
  useEffect(() => { void load(); }, [load]);
  const cards: [string, number, string][] = stats ? [
    ["Total complaints", stats.total, "All stored reports"], ["Submitted", stats.submitted, "Waiting for review"], ["Under review", stats.under_review, "Being assessed"],
    ["In progress", stats.in_progress, "Work underway"], ["Resolved", stats.resolved, "Marked complete"], ["Rejected", stats.rejected, "Not accepted"],
    ["Last 7 days", stats.submitted_last_7_days, "Recent submissions"], ["With photo", stats.with_photo, "Evidence attached"], ["With location", stats.with_location, "Place confirmed"],
  ] : [];
  return <><section className="admin-title"><div><p className="eyebrow">Municipal workspace</p><h1>Operations dashboard</h1><p>Review the current complaint workload and move reports through the verified lifecycle.</p></div><AdminLink href="/admin/complaints" navigate={navigate} className="admin-primary-link">Open my work</AdminLink></section>{work && <section aria-labelledby="my-work-heading"><h2 id="my-work-heading">My work</h2><div className="stat-grid"><article className="stat-card"><strong>{work.assigned_to_me}</strong><div><span>Assigned to me</span><small>Individual responsibility</small></div></article><article className="stat-card"><strong>{work.unassigned_in_my_departments}</strong><div><span>Department queue</span><small>Available to claim</small></div></article><article className="stat-card"><strong>{work.in_progress_assigned_to_me}</strong><div><span>My in-progress work</span><small>Work underway</small></div></article>{session.user.role === "municipal_admin" && <article className="stat-card"><strong>{work.unassigned_department}</strong><div><span>No department</span><small>Needs organizational triage</small></div></article>}</div>{session.user.role === "municipal_admin" && work.departments.length > 0 && <div className="admin-table-wrap"><table><caption>Department workload</caption><thead><tr><th>Department</th><th>Unresolved</th><th>Assigned</th><th>Department queue</th></tr></thead><tbody>{work.departments.map((row) => <tr key={row.department.department_id}><td>{row.department.display_name}{row.department.is_active ? "" : " (inactive)"}</td><td>{row.unresolved}</td><td>{row.assigned}</td><td>{row.unassigned}</td></tr>)}</tbody></table></div>}</section>}<section aria-labelledby="statistics-heading"><h2 id="statistics-heading">Current operational totals</h2>{loading && !stats && <div className="admin-state" role="status">Loading complaint statistics…</div>}{error && <div className="admin-state admin-error" role="alert"><strong>Statistics unavailable</strong><p>{error}</p><button type="button" onClick={() => void load()}>Try again</button></div>}{stats && stats.total === 0 && <div className="admin-state"><strong>No complaints yet</strong><p>Submitted citizen complaints will appear in the municipal queue.</p></div>}{stats && <div className="stat-grid">{cards.map(([label, value, context]) => <article className="stat-card" key={label}><strong>{value}</strong><div><span>{label}</span><small>{context}</small></div></article>)}</div>}</section><p className="admin-disclaimer">These are stored operational totals—not AI categories, priorities, service targets or department-performance metrics.</p></>;
}

function ComplaintResult({ complaint, navigate }: { complaint: AdminComplaint; navigate: (path: string) => void }) {
  return <article className="admin-complaint-card"><div className="admin-card-heading"><strong>#{complaint.complaint_id.slice(0, 8)}</strong><StatusBadge status={complaint.status} /></div><p>{complaint.description}</p><dl><div><dt>Department</dt><dd>{complaint.department?.display_name ?? "Unassigned"}</dd></div><div><dt>Responsible</dt><dd>{complaint.assignee ? `${complaint.assignee.username}${complaint.assignee.is_active ? "" : " (inactive)"}` : "Department queue"}</dd></div><div><dt>Submitted</dt><dd>{readableDate(complaint.created_at)}</dd></div></dl><AdminLink href={`/admin/complaints/${complaint.complaint_id}`} navigate={navigate} className="card-action">Open complaint <span aria-hidden="true">→</span></AdminLink></article>;
}

function ComplaintTable({ navigate, onExpired, session }: { navigate: (path: string) => void; onExpired: () => void; session: AuthSession }) {
  useDocumentTitle("Complaint queue | CivicAI");
  const [pageData, setPageData] = useState<AdminComplaintPage>(); const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ComplaintStatus | "">(""); const [query, setQuery] = useState(""); const [submittedQuery, setSubmittedQuery] = useState("");
  const [photo, setPhoto] = useState(""); const [location, setLocation] = useState(""); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [queue, setQueue] = useState<"" | "unassigned" | "mine" | "my_departments_unassigned">(session.user.role === "municipal_operator" ? "mine" : "");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setPageData(await listAdminComplaints({ page, pageSize: 10, status, query: submittedQuery, hasPhoto: photo === "yes" ? true : photo === "no" ? false : undefined, hasLocation: location === "yes" ? true : location === "no" ? false : undefined, queue: queue || undefined })); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Complaints could not be loaded."); }
    finally { setLoading(false); }
  }, [page, status, submittedQuery, photo, location, queue, onExpired]);
  useEffect(() => { void load(); }, [load]);
  const activeFilterCount = [submittedQuery.trim(), status, photo, location, queue].filter(Boolean).length;
  const clear = () => { setQuery(""); setSubmittedQuery(""); setStatus(""); setPhoto(""); setLocation(""); setQueue(session.user.role === "municipal_operator" ? "mine" : ""); setPage(1); };
  return <section className="admin-complaints" aria-labelledby="complaints-title"><div className="admin-title"><div><p className="eyebrow">Municipal queue</p><h1 id="complaints-title">Complaints</h1><p>Search and filter stored reports. Open one complaint to inspect its evidence and history.</p></div></div>
    <div className="queue-tabs" role="group" aria-label="Work queue"><button type="button" aria-pressed={queue === "mine"} onClick={() => { setQueue("mine"); setPage(1); }}>Assigned to me</button><button type="button" aria-pressed={queue === "my_departments_unassigned"} onClick={() => { setQueue("my_departments_unassigned"); setPage(1); }}>Department queue</button>{session.user.role === "municipal_admin" && <><button type="button" aria-pressed={queue === "unassigned"} onClick={() => { setQueue("unassigned"); setPage(1); }}>No department</button><button type="button" aria-pressed={queue === ""} onClick={() => { setQueue(""); setPage(1); }}>All complaints</button></>}</div>
    <form className="admin-filters" onSubmit={(event) => { event.preventDefault(); setPage(1); setSubmittedQuery(query); }} aria-label="Complaint filters"><label>Search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Reference, description or place" /></label><label>Status<select value={status} onChange={(event) => { setStatus(event.target.value as ComplaintStatus | ""); setPage(1); }}><option value="">All statuses</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Photo<select value={photo} onChange={(event) => { setPhoto(event.target.value); setPage(1); }}><option value="">Any</option><option value="yes">With photo</option><option value="no">Without photo</option></select></label><label>Location<select value={location} onChange={(event) => { setLocation(event.target.value); setPage(1); }}><option value="">Any</option><option value="yes">With location</option><option value="no">Without location</option></select></label><div className="filter-actions"><button type="submit">Apply filters</button><button type="button" onClick={clear} disabled={!activeFilterCount && !query}>Reset</button></div></form>
    <div className="filter-summary" role="status" aria-live="polite">{activeFilterCount ? `${activeFilterCount} filter${activeFilterCount === 1 ? "" : "s"} active` : "No filters active"}{pageData && !loading ? ` · ${pageData.total} result${pageData.total === 1 ? "" : "s"}` : ""}</div>
    {loading && !pageData && <div className="admin-state" role="status">Loading complaints…</div>}{error && <div className="admin-state admin-error" role="alert"><strong>Complaint queue unavailable</strong><p>{error}</p><button type="button" onClick={() => void load()}>Try again</button></div>}
    {!loading && !error && pageData?.items.length === 0 && <div className="admin-state"><strong>{activeFilterCount ? "No complaints match these filters" : "No complaints yet"}</strong><p>{activeFilterCount ? "Clear or change a filter to broaden the results." : "Citizen submissions will appear here."}</p>{activeFilterCount > 0 && <button type="button" onClick={clear}>Clear filters</button>}</div>}
    {pageData && pageData.items.length > 0 && <><div className="admin-table-wrap"><table><caption className="sr-only">Filtered municipal complaint results</caption><thead><tr><th scope="col">Complaint</th><th scope="col">Department</th><th scope="col">Responsible</th><th scope="col">Status</th><th scope="col"><span className="sr-only">Action</span></th></tr></thead><tbody>{pageData.items.map((complaint) => <tr key={complaint.complaint_id}><td><strong>#{complaint.complaint_id.slice(0, 8)}</strong><span>{complaint.description}</span></td><td>{complaint.department?.display_name ?? "Unassigned"}</td><td>{complaint.assignee ? `${complaint.assignee.username}${complaint.assignee.is_active ? "" : " (inactive)"}` : "Department queue"}</td><td><StatusBadge status={complaint.status} /></td><td><AdminLink href={`/admin/complaints/${complaint.complaint_id}`} navigate={navigate} aria-label={`Open complaint ${complaint.complaint_id.slice(0, 8)}`}>Open</AdminLink></td></tr>)}</tbody></table></div><div className="admin-mobile-list" role="region" aria-label="Complaint results">{pageData.items.map((complaint) => <ComplaintResult key={complaint.complaint_id} complaint={complaint} navigate={navigate} />)}</div><div className="pagination" aria-label="Complaint pages"><button type="button" disabled={page <= 1 || loading} onClick={() => setPage((value) => value - 1)}>Previous</button><span>Page {pageData.page} of {Math.max(pageData.total_pages, 1)} · {pageData.total} complaints</span><button type="button" disabled={pageData.page >= pageData.total_pages || loading} onClick={() => setPage((value) => value + 1)}>Next</button></div></>}
  </section>;
}

function ComplaintDetail({ complaintId, navigate, session, onExpired }: { complaintId: string; navigate: (path: string) => void; session: AuthSession; onExpired: () => void }) {
  useDocumentTitle("Complaint details | CivicAI");
  const [complaint, setComplaint] = useState<Awaited<ReturnType<typeof getAdminComplaint>>>(); const [error, setError] = useState(""); const [imageFailed, setImageFailed] = useState(false);
  const [target, setTarget] = useState<ComplaintStatus>(); const [note, setNote] = useState(""); const [saving, setSaving] = useState(false); const [success, setSuccess] = useState(""); const [confirmReject, setConfirmReject] = useState(false); const updateButton = useRef<HTMLButtonElement>(null);
  const [departments, setDepartments] = useState<MunicipalDepartment[]>([]); const [users, setUsers] = useState<MunicipalUser[]>([]);
  const [departmentId, setDepartmentId] = useState(""); const [assigneeId, setAssigneeId] = useState(""); const [assignmentReason, setAssignmentReason] = useState("");
  const load = useCallback(async () => {
    setError("");
    try { const loaded = await getAdminComplaint(complaintId); setComplaint(loaded); setDepartmentId(loaded.department?.department_id ?? ""); setAssigneeId(loaded.assignee?.user_id ?? ""); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Complaint could not be loaded."); }
  }, [complaintId, onExpired]);
  useEffect(() => { void load(); void listDepartments().then(setDepartments).catch(() => undefined); if (session.user.role === "municipal_admin") void listUsers().then(setUsers).catch(() => undefined); }, [load, session.user.role]); useEffect(() => { setTarget(undefined); setNote(""); setImageFailed(false); }, [complaintId]);
  async function saveStatus() {
    if (!complaint || !target) return; setSaving(true); setError(""); setSuccess("");
    try { await updateComplaintStatus(complaint.complaint_id, { newStatus: target, expectedUpdatedAt: complaint.updated_at, operatorNote: note }, session.csrf_token); await load(); setTarget(undefined); setNote(""); setConfirmReject(false); setSuccess("Status updated and recorded in history."); }
    catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) onExpired();
      else if (reason instanceof ApiError && reason.status === 409) setError("This complaint changed since you opened it. Your note is still here. Reload the latest details before trying again.");
      else setError(reason instanceof Error ? reason.message : "Status could not be updated.");
    } finally { setSaving(false); }
  }
  function submitStatus(event: FormEvent) { event.preventDefault(); if (!target) return; if (target === "rejected") setConfirmReject(true); else void saveStatus(); }
  async function saveAssignment(event: FormEvent) {
    event.preventDefault(); if (!complaint || session.user.role !== "municipal_admin") return; setSaving(true); setError(""); setSuccess("");
    try { await updateComplaintAssignment(complaint.complaint_id, { departmentId: departmentId || null, assigneeUserId: assigneeId || null, expectedUpdatedAt: complaint.updated_at, reason: assignmentReason }, session.csrf_token); await load(); setAssignmentReason(""); setSuccess("Ownership updated and recorded in assignment history."); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else if (reason instanceof ApiError && reason.status === 409) setError("This complaint was changed by another municipal user. Your reason is still here; reload before trying again."); else setError(reason instanceof Error ? reason.message : "Assignment could not be updated."); }
    finally { setSaving(false); }
  }
  async function claim() {
    if (!complaint) return; setSaving(true); setError("");
    try { await claimComplaint(complaint.complaint_id, complaint.updated_at, session.csrf_token); await load(); setSuccess("Complaint assigned to you."); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else if (reason instanceof ApiError && reason.status === 409) setError("Another municipal user changed or claimed this complaint. Reload the latest details."); else setError(reason instanceof Error ? reason.message : "Complaint could not be claimed."); }
    finally { setSaving(false); }
  }
  if (error && !complaint) return <section className="admin-state admin-error" role="alert"><strong>Complaint unavailable</strong><p>{error}</p><button onClick={() => void load()}>Try again</button></section>;
  if (!complaint) return <div className="admin-state" role="status">Loading complaint…</div>;
  const hasCoordinates = complaint.latitude !== null && complaint.longitude !== null;
  return <section className="admin-detail"><AdminLink href="/admin/complaints" navigate={navigate} className="back-link">← Back to complaints</AdminLink><div className="detail-heading"><div><p className="eyebrow">Complaint #{complaint.complaint_id.slice(0, 8)}</p><h1>{complaint.description}</h1></div><StatusBadge status={complaint.status} /></div>
    {error && <div className="admin-state admin-error" role="alert"><strong>Update not completed</strong><p>{error}</p><button onClick={() => void load()}>Reload latest details</button></div>}{success && <div className="admin-success" role="status">{success}</div>}
    <div className="detail-grid"><article className="detail-card evidence-card"><h2>Complaint evidence</h2><dl><div><dt>Full reference</dt><dd>{complaint.complaint_id}</dd></div><div><dt>Submitted</dt><dd>{readableDate(complaint.created_at)}</dd></div></dl>{complaint.image_ref && !imageFailed ? <img src={imageUrl(complaint.image_ref)} alt="Citizen-submitted complaint evidence" loading="lazy" decoding="async" width="960" height="540" onError={() => setImageFailed(true)} /> : <div className="evidence-placeholder">{imageFailed ? "Photo evidence could not be loaded." : "No photo evidence is stored."}</div>}</article>
      <article className="detail-card"><h2>Issue location</h2><p className="location-label">{complaint.location_label ?? "No location was provided."}</p>{complaint.location_details && <p>{complaint.location_details}</p>}{complaint.location_precision && <p className="detail-muted">{complaint.location_precision === "exact" ? "Confirmed point" : complaint.location_precision === "broad" ? "Broad area" : "Approximate place"} · selected by {complaint.location_source === "device" ? "device location" : complaint.location_source === "map" ? "map adjustment" : "place search"}</p>}{hasCoordinates ? <Suspense fallback={<div className="map-loading" role="status">Loading submitted-location map…</div>}><ReadOnlyLocationMap latitude={complaint.latitude!} longitude={complaint.longitude!} readOnly /></Suspense> : <div className="evidence-placeholder">Map unavailable because this complaint has no coordinates.</div>}{hasCoordinates && <details><summary>Technical coordinates</summary><p>{complaint.latitude}, {complaint.longitude}</p></details>}</article></div>
    <div className="detail-grid operations-grid"><article className="detail-card"><h2>Update status</h2><form onSubmit={submitStatus}><label htmlFor="next-status">Next status</label><select id="next-status" value={target ?? ""} onChange={(event) => setTarget(event.target.value as ComplaintStatus)} required><option value="">Choose an allowed transition</option>{allowedTransitions[complaint.status].map((value) => <option key={value} value={value}>{statusLabels[value]}</option>)}</select><label htmlFor="operator-note">Internal operator note <span>Optional</span></label><textarea id="operator-note" value={note} onChange={(event) => setNote(event.target.value)} maxLength={1000} rows={4} placeholder="Example: Site inspected; repair crew notified" /><p className="detail-muted">Only authenticated municipal staff can see this note. The update records your account ID.</p><button ref={updateButton} type="submit" disabled={!target || saving}>{saving ? "Saving update…" : "Record status change"}</button></form></article>
      <article className="detail-card"><h2>Status history</h2>{complaint.history.length ? <ol className="history-list">{complaint.history.map((event) => <li key={event.event_id}><span className="history-dot" aria-hidden="true" /><div><strong>{event.event_type === "created" ? "Complaint submitted" : `${statusLabels[event.previous_status!]} → ${statusLabels[event.new_status]}`}</strong><time dateTime={event.occurred_at}>{readableDate(event.occurred_at)}</time>{event.actor_id && <small>Operator ID: {event.actor_id.slice(0, 8)}</small>}{event.operator_note && <p>{event.operator_note}</p>}</div></li>)}</ol> : <div className="evidence-placeholder">No status history is available.</div>}</article></div>
    <div className="detail-grid operations-grid"><article className="detail-card"><h2>Ownership and responsibility</h2><dl><div><dt>Owning department</dt><dd>{complaint.department ? `${complaint.department.display_name}${complaint.department.is_active ? "" : " (inactive)"}` : "No department assigned"}</dd></div><div><dt>Assigned operator</dt><dd>{complaint.assignee ? `${complaint.assignee.username}${complaint.assignee.is_active ? "" : " (inactive — reassign required)"}` : "Nobody — available in the department queue"}</dd></div></dl>{session.user.role === "municipal_admin" ? <form onSubmit={saveAssignment}><label htmlFor="owner-department">Department</label><select id="owner-department" value={departmentId} onChange={(event) => { setDepartmentId(event.target.value); setAssigneeId(""); }}><option value="">No department</option>{departments.filter((item) => item.is_active || item.department_id === complaint.department?.department_id).map((item) => <option key={item.department_id} value={item.department_id}>{item.display_name}{item.is_active ? "" : " (inactive)"}</option>)}</select><label htmlFor="owner-operator">Assigned operator <span>Optional</span></label><select id="owner-operator" value={assigneeId} onChange={(event) => setAssigneeId(event.target.value)} disabled={!departmentId}><option value="">Department queue</option>{users.filter((user) => departments.find((item) => item.department_id === departmentId)?.members.some((member) => member.user_id === user.user_id)).map((user) => <option key={user.user_id} value={user.user_id}>{user.username}{user.is_active ? "" : " (inactive)"}</option>)}</select><label htmlFor="assignment-reason">Assignment reason <span>Optional</span></label><textarea id="assignment-reason" value={assignmentReason} onChange={(event) => setAssignmentReason(event.target.value)} maxLength={1000} rows={3} /><button disabled={saving}>Save ownership</button></form> : !complaint.assignee && complaint.department ? <button type="button" disabled={saving} onClick={() => void claim()}>Assign to me</button> : null}</article>
      <article className="detail-card"><h2>Assignment history</h2>{complaint.assignment_history.length ? <ol className="history-list">{complaint.assignment_history.map((event) => <li key={event.event_id}><span className="history-dot" aria-hidden="true" /><div><strong>{event.event_type.replaceAll("_", " ")}</strong><time dateTime={event.occurred_at}>{readableDate(event.occurred_at)}</time><small>Changed by {event.actor_user_id.slice(0, 8)}</small>{event.reason && <p>{event.reason}</p>}</div></li>)}</ol> : <div className="evidence-placeholder">No ownership changes have been recorded.</div>}</article></div>
    <ConfirmDialog open={confirmReject} title="Reject this complaint?" description={<p>The complaint will be marked Rejected and this action will be recorded in its history. You can restore it to review later.</p>} confirmLabel="Reject complaint" destructive busy={saving} returnFocusRef={updateButton} onCancel={() => setConfirmReject(false)} onConfirm={() => void saveStatus()} />
  </section>;
}

type PendingUserAction = { user: MunicipalUser; input: { role?: MunicipalRole; is_active?: boolean }; title: string; description: string; confirmLabel: string; destructive: boolean };

function StaffManagement({ session, onExpired }: { session: AuthSession; onExpired: () => void }) {
  useDocumentTitle("Municipal staff | CivicAI");
  const [users, setUsers] = useState<MunicipalUser[]>([]); const [invitations, setInvitations] = useState<StaffInvitation[]>([]); const [departments, setDepartments] = useState<MunicipalDepartment[]>([]);
  const [email, setEmail] = useState(""); const [role, setRole] = useState<MunicipalRole>("municipal_operator"); const [departmentIds, setDepartmentIds] = useState<string[]>([]);
  const [error, setError] = useState(""); const [success, setSuccess] = useState(""); const [saving, setSaving] = useState(false);
  const [pending, setPending] = useState<PendingUserAction>(); const actionButton = useRef<HTMLElement>(null);
  const load = useCallback(async () => {
    try { const [nextUsers, nextInvites, nextDepartments] = await Promise.all([listUsers(), listStaffInvitations(), listDepartments(false)]); setUsers(nextUsers); setInvitations(nextInvites); setDepartments(nextDepartments); setError(""); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Municipal staff could not be loaded."); }
  }, [onExpired]);
  useEffect(() => { void load(); }, [load]);
  async function submit(event: FormEvent) { event.preventDefault(); setSaving(true); setError(""); setSuccess(""); try { await inviteStaff({ email, role, department_ids: departmentIds }, session.csrf_token); setEmail(""); setDepartmentIds([]); await load(); setSuccess("Invitation sent through the configured email service."); } catch (reason) { setError(reason instanceof Error ? reason.message : "Invitation could not be created."); } finally { setSaving(false); } }
  async function revoke(invitation: StaffInvitation) { setSaving(true); try { await revokeStaffInvitation(invitation.invitation_id, session.csrf_token); await load(); setSuccess("Pending invitation revoked."); } catch (reason) { setError(reason instanceof Error ? reason.message : "Invitation could not be revoked."); } finally { setSaving(false); } }
  async function applyPending() { if (!pending) return; setSaving(true); setError(""); try { await updateUser(pending.user.user_id, pending.input, session.csrf_token); await load(); setSuccess(`${pending.user.username} was updated.`); setPending(undefined); } catch (reason) { setError(reason instanceof Error ? reason.message : "Account could not be updated."); } finally { setSaving(false); } }
  function requestRole(user: MunicipalUser, next: MunicipalRole, element: HTMLElement) { actionButton.current = element; setPending({ user, input: { role: next }, title: `Change ${user.username}'s role?`, description: `${user.username} will become ${roleLabels[next].toLowerCase()}. Their permissions will change immediately.`, confirmLabel: "Change role", destructive: next === "municipal_operator" }); }
  function requestActive(user: MunicipalUser, element: HTMLElement) { actionButton.current = element; if (!user.is_active) { void updateUser(user.user_id, { is_active: true }, session.csrf_token).then(async () => { await load(); setSuccess(`${user.username} was reactivated.`); }).catch((reason) => setError(reason instanceof Error ? reason.message : "Account could not be reactivated.")); return; } setPending({ user, input: { is_active: false }, title: `Disable ${user.username}?`, description: "The account will be unable to sign in and its active sessions will be revoked. Its audit history will remain.", confirmLabel: "Disable account", destructive: true }); }
  return <section className="admin-users"><div className="admin-title"><div><p className="eyebrow">Administrator only</p><h1>Municipal Staff</h1><p>Invite approved staff. Recipients choose their own password; role and departments stay under administrator control.</p></div></div>{error && <div className="admin-state admin-error" role="alert"><strong>Staff action not completed</strong><p>{error}</p></div>}{success && <div className="admin-success" role="status">{success}</div>}<div className="user-management-grid"><article className="detail-card"><h2>Invite staff member</h2><form onSubmit={submit}><label htmlFor="invite-email">Work email</label><input id="invite-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required /><label htmlFor="invite-role">Role</label><select id="invite-role" value={role} onChange={(event) => setRole(event.target.value as MunicipalRole)}><option value="municipal_operator">Municipal operator</option><option value="municipal_admin">Municipal administrator</option></select><fieldset className="invite-departments"><legend>Initial departments</legend>{departments.map((department) => <label key={department.department_id}><input type="checkbox" checked={departmentIds.includes(department.department_id)} onChange={(event) => setDepartmentIds((current) => event.target.checked ? [...current, department.department_id] : current.filter((id) => id !== department.department_id))} /> {department.display_name}</label>)}</fieldset><button disabled={saving}>{saving ? "Sending invitation…" : "Invite staff member"}</button></form></article><article className="detail-card account-list"><h2>Existing staff</h2>{users.map((user) => <div className="account-row" key={user.user_id}><div><strong>{user.display_name || user.username}</strong><small>{user.username} · {roleLabels[user.role]} · {user.is_active ? "Active" : "Disabled"}</small></div><select aria-label={`Role for ${user.username}`} value={user.role} disabled={user.user_id === session.user.user_id || saving} onChange={(event) => requestRole(user, event.target.value as MunicipalRole, event.currentTarget)}><option value="municipal_operator">Operator</option><option value="municipal_admin">Administrator</option></select><button type="button" disabled={user.user_id === session.user.user_id || saving} onClick={(event) => requestActive(user, event.currentTarget)}>{user.is_active ? "Disable" : "Reactivate"}</button></div>)}</article></div><article className="detail-card"><h2>Invitations</h2>{invitations.length === 0 ? <p>No staff invitations yet.</p> : invitations.map((invitation) => <div className="account-row" key={invitation.invitation_id}><div><strong>{invitation.email}</strong><small>{roleLabels[invitation.role]} · {invitation.accepted_at ? "Accepted" : invitation.revoked_at ? "Revoked" : "Pending"}</small></div>{!invitation.accepted_at && !invitation.revoked_at && <button type="button" disabled={saving} onClick={() => void revoke(invitation)}>Revoke</button>}</div>)}</article><ConfirmDialog open={Boolean(pending)} title={pending?.title ?? "Confirm account change"} description={<p>{pending?.description}</p>} confirmLabel={pending?.confirmLabel ?? "Confirm"} destructive={pending?.destructive} busy={saving} returnFocusRef={actionButton} onCancel={() => setPending(undefined)} onConfirm={() => void applyPending()} /></section>;
}

function DepartmentManagement({ session, onExpired }: { session: AuthSession; onExpired: () => void }) {
  useDocumentTitle("Municipal departments | CivicAI");
  const [departments, setDepartments] = useState<MunicipalDepartment[]>([]); const [users, setUsers] = useState<MunicipalUser[]>([]);
  const [name, setName] = useState(""); const [slug, setSlug] = useState(""); const [description, setDescription] = useState("");
  const [error, setError] = useState(""); const [success, setSuccess] = useState(""); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => {
    try { const [departmentRows, userRows] = await Promise.all([listDepartments(true), listUsers()]); setDepartments(departmentRows); setUsers(userRows); setError(""); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Departments could not be loaded."); }
  }, [onExpired]);
  useEffect(() => { void load(); }, [load]);
  async function submit(event: FormEvent) { event.preventDefault(); setSaving(true); setError(""); try { await createDepartment({ slug, display_name: name, description: description || undefined }, session.csrf_token); setName(""); setSlug(""); setDescription(""); await load(); setSuccess("Department created."); } catch (reason) { setError(reason instanceof Error ? reason.message : "Department could not be created."); } finally { setSaving(false); } }
  async function toggle(department: MunicipalDepartment) { setSaving(true); setError(""); try { await updateDepartment(department.department_id, { is_active: !department.is_active }, session.csrf_token); await load(); setSuccess(`${department.display_name} ${department.is_active ? "deactivated" : "reactivated"}.`); } catch (reason) { setError(reason instanceof Error ? reason.message : "Department could not be updated."); } finally { setSaving(false); } }
  async function changeMember(department: MunicipalDepartment, userId: string, add: boolean) { setSaving(true); setError(""); try { if (add) await addDepartmentMember(department.department_id, userId, session.csrf_token); else await removeDepartmentMember(department.department_id, userId, session.csrf_token); await load(); setSuccess("Department membership updated."); } catch (reason) { setError(reason instanceof Error ? reason.message : "Membership could not be updated."); } finally { setSaving(false); } }
  return <section className="admin-users"><div className="admin-title"><div><p className="eyebrow">Administrator only</p><h1>Departments and membership</h1><p>Manage operational units independently from authentication roles.</p></div></div>{error && <div className="admin-state admin-error" role="alert"><strong>Department action not completed</strong><p>{error}</p></div>}{success && <div className="admin-success" role="status">{success}</div>}<div className="user-management-grid"><article className="detail-card"><h2>Create department</h2><form onSubmit={submit}><label htmlFor="department-name">Display name</label><input id="department-name" value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={100} required /><label htmlFor="department-slug">Stable slug</label><input id="department-slug" value={slug} onChange={(event) => setSlug(event.target.value.toLowerCase())} pattern="[a-z0-9]+(-[a-z0-9]+)*" minLength={2} maxLength={64} required /><p className="detail-muted">Lowercase words separated by hyphens. The slug cannot be renamed.</p><label htmlFor="department-description">Description <span>Optional</span></label><textarea id="department-description" value={description} onChange={(event) => setDescription(event.target.value)} maxLength={500} rows={3} /><button disabled={saving}>Create department</button></form></article><article className="detail-card account-list"><h2>Existing departments</h2>{departments.length === 0 ? <div className="evidence-placeholder">No departments exist. Create the first real operational unit.</div> : departments.map((department) => <div className="department-row" key={department.department_id}><div><strong>{department.display_name}</strong><small>{department.slug} · {department.is_active ? "Active" : "Inactive"}</small>{department.description && <p>{department.description}</p>}</div><label>Members<select aria-label={`Add member to ${department.display_name}`} defaultValue="" disabled={!department.is_active || saving} onChange={(event) => { if (event.target.value) void changeMember(department, event.target.value, true); event.target.value = ""; }}><option value="">Add an active account…</option>{users.filter((user) => user.is_active && !department.members.some((member) => member.user_id === user.user_id)).map((user) => <option key={user.user_id} value={user.user_id}>{user.username}</option>)}</select></label><ul className="member-list">{department.members.map((member) => <li key={member.user_id}><span>{member.username}{member.is_active ? "" : " (inactive)"}</span><button type="button" disabled={saving} onClick={() => void changeMember(department, member.user_id, false)}>Remove</button></li>)}</ul><button type="button" className={department.is_active ? "danger-button" : ""} disabled={saving} onClick={() => void toggle(department)}>{department.is_active ? "Deactivate" : "Reactivate"}</button></div>)}</article></div></section>;
}

function AdminNotFound({ navigate }: { navigate: (path: string) => void }) {
  useDocumentTitle("Page not found | CivicAI Operations");
  return <section className="route-state admin-route-state"><p className="eyebrow">Page not found</p><h1>That municipal page does not exist</h1><p>Return to the dashboard or complaint queue.</p><div className="route-actions"><AdminLink href="/admin" navigate={navigate} className="admin-primary-link">Go to dashboard</AdminLink><AdminLink href="/admin/complaints" navigate={navigate}>Open complaints</AdminLink></div></section>;
}

export default function AdminApp() {
  const [path, navigate] = usePathname(); const [session, setSession] = useState<AuthSession>(); const [loading, setLoading] = useState(true); const [startupError, setStartupError] = useState(""); const [authMessage, setAuthMessage] = useState("");
  const intendedPath = path === "/admin/login" ? "/admin" : path;
  const verify = useCallback(async () => {
    setLoading(true); setStartupError("");
    try { const current = await getSession(); setSession(current); if (["/admin/login", "/staff/sign-in"].includes(window.location.pathname)) navigate("/admin"); }
    catch (reason) { setSession(undefined); if (!(reason instanceof ApiError && reason.status === 401)) setStartupError(reason instanceof Error ? reason.message : "Authentication service unavailable."); }
    finally { setLoading(false); }
  }, [navigate]);
  useEffect(() => { void verify(); }, [verify]);
  const expired = useCallback(() => { setSession(undefined); setAuthMessage("Your municipal session ended. Sign in again to continue."); navigate("/admin/login"); }, [navigate]);
  if (loading) return <main className="admin-login-page" id="main-content"><div className="admin-state" role="status">Verifying municipal session…</div></main>;
  if (!session) return <><a className="skip-link" href="#main-content">Skip to main content</a><LoginPage returnTo={intendedPath} message={authMessage} onAuthenticated={(nextSession, returnTo) => { setSession(nextSession); setAuthMessage(""); navigate(returnTo); }} />{startupError && <div className="admin-login-outage" role="alert"><strong>Sign-in service unavailable</strong><p>{startupError}</p><button type="button" onClick={() => void verify()}>Try again</button></div>}</>;
  const match = path.match(/^\/admin\/complaints\/([^/]+)$/); let content: ReactNode;
  if (path === "/admin") content = <Dashboard navigate={navigate} onExpired={expired} session={session} />;
  else if (path === "/admin/complaints") content = <ComplaintTable navigate={navigate} onExpired={expired} session={session} />;
  else if (match) content = <ComplaintDetail complaintId={decodeURIComponent(match[1])} navigate={navigate} session={session} onExpired={expired} />;
  else if (path === "/admin/users") content = session.user.role === "municipal_admin" ? <StaffManagement session={session} onExpired={expired} /> : <section className="admin-state admin-error" role="alert"><strong>Administrator permission required</strong><p>Your account can review complaints but cannot manage municipal accounts.</p></section>;
  else if (path === "/admin/departments") content = session.user.role === "municipal_admin" ? <DepartmentManagement session={session} onExpired={expired} /> : <section className="admin-state admin-error" role="alert"><strong>Administrator permission required</strong><p>Your account cannot manage departments.</p></section>;
  else content = <AdminNotFound navigate={navigate} />;
  return <AdminShell path={path} navigate={navigate} session={session} onLogout={async () => { try { await logout(session.csrf_token); } finally { setSession(undefined); setAuthMessage("You have signed out."); navigate("/admin/login"); } }}>{content}</AdminShell>;
}
