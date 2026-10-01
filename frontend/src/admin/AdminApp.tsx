import { FormEvent, ReactNode, Suspense, lazy, useCallback, useEffect, useState } from "react";
import {
  AdminComplaintPage, ApiError, ComplaintStatus, DashboardStatistics,
  getAdminComplaint, getDashboardStatistics, imageUrl, listAdminComplaints,
  updateComplaintStatus,
} from "../api/complaints";
import {
  AuthSession, MunicipalRole, MunicipalUser, createUser, getSession, listUsers,
  login, logout, updateUser,
} from "../api/auth";

const ReadOnlyLocationMap = lazy(() => import("../LocationMap"));

function readableDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

const statusLabels: Record<ComplaintStatus, string> = {
  submitted: "Submitted", under_review: "Under review", in_progress: "In progress",
  resolved: "Resolved", rejected: "Rejected",
};

const roleLabels: Record<MunicipalRole, string> = {
  municipal_operator: "Municipal operator", municipal_admin: "Municipal administrator",
};

const allowedTransitions: Record<ComplaintStatus, ComplaintStatus[]> = {
  submitted: ["under_review", "rejected"], under_review: ["in_progress", "rejected"],
  in_progress: ["under_review", "resolved", "rejected"], resolved: ["under_review"],
  rejected: ["under_review"],
};

function usePathname() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const change = () => setPath(window.location.pathname);
    window.addEventListener("popstate", change);
    return () => window.removeEventListener("popstate", change);
  }, []);
  const navigate = useCallback((next: string) => {
    window.history.pushState({}, "", next); setPath(next); window.scrollTo({ top: 0 });
  }, []);
  return [path, navigate] as const;
}

function AdminLink({ href, children, className, navigate }: {
  href: string; children: ReactNode; className?: string; navigate: (path: string) => void;
}) {
  return <a href={href} className={className} onClick={(event) => {
    if (!event.ctrlKey && !event.metaKey && !event.shiftKey) { event.preventDefault(); navigate(href); }
  }}>{children}</a>;
}

function StatusPill({ status }: { status: ComplaintStatus }) {
  return <span className={`admin-status status-${status}`}>{statusLabels[status]}</span>;
}

function LoginPage({ returnTo, onAuthenticated }: {
  returnTo: string; onAuthenticated: (session: AuthSession, path: string) => void;
}) {
  const [username, setUsername] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [submitting, setSubmitting] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setSubmitting(true); setError("");
    try { onAuthenticated(await login(username, password), returnTo); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Sign in failed."); }
    finally { setSubmitting(false); }
  }
  return <main className="admin-login-page"><section className="admin-login-card" aria-labelledby="login-title">
    <a href="/" className="admin-brand">Civic<span>AI</span> Operations</a>
    <p className="eyebrow">Restricted municipal workspace</p><h1 id="login-title">Municipal sign in</h1>
    <p>Use the account created by your municipal administrator. Citizen complaint submission remains anonymous.</p>
    {error && <div className="admin-state admin-error" role="alert">{error}</div>}
    <form onSubmit={submit}><label htmlFor="admin-username">Username</label><input id="admin-username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /><label htmlFor="admin-password">Password</label><input id="admin-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /><button type="submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button></form>
    <a href="/">Return to citizen portal</a>
  </section></main>;
}

function AdminShell({ children, navigate, session, onLogout }: {
  children: ReactNode; navigate: (path: string) => void; session: AuthSession; onLogout: () => Promise<void>;
}) {
  return <main className="admin-app"><header className="admin-header">
    <AdminLink href="/admin" navigate={navigate} className="admin-brand">Civic<span>AI</span> Operations</AdminLink>
    <nav aria-label="Municipal navigation"><AdminLink href="/admin" navigate={navigate}>Dashboard</AdminLink><AdminLink href="/admin/complaints" navigate={navigate}>Complaints</AdminLink>{session.user.role === "municipal_admin" && <AdminLink href="/admin/users" navigate={navigate}>Accounts</AdminLink>}<a href="/">Citizen view</a></nav>
    <div className="admin-identity"><span>{session.user.username}<small>{roleLabels[session.user.role]}</small></span><button type="button" onClick={() => void onLogout()}>Sign out</button></div>
  </header>{children}<footer><span>CivicAI municipal operations</span><span>Authenticated operational data · no ML predictions</span></footer></main>;
}

function Dashboard({ navigate, onExpired }: { navigate: (path: string) => void; onExpired: () => void }) {
  const [stats, setStats] = useState<DashboardStatistics>(); const [error, setError] = useState("");
  useEffect(() => { getDashboardStatistics().then(setStats).catch((reason) => { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Dashboard statistics could not be loaded."); }); }, [onExpired]);
  const cards: [string, number][] = stats ? [["Total complaints", stats.total], ["Submitted", stats.submitted], ["Under review", stats.under_review], ["In progress", stats.in_progress], ["Resolved", stats.resolved], ["Rejected", stats.rejected], ["Last 7 days", stats.submitted_last_7_days], ["With photo", stats.with_photo], ["With location", stats.with_location]] : [];
  return <><section className="admin-title"><div><p className="eyebrow">Municipal workspace</p><h1>Operations dashboard</h1></div><AdminLink href="/admin/complaints" navigate={navigate} className="admin-primary-link">Review complaints</AdminLink></section><section aria-labelledby="statistics-heading"><h2 id="statistics-heading">Current operational totals</h2>{!stats && !error && <div className="admin-state">Loading real complaint statistics…</div>}{error && <div className="admin-state admin-error" role="alert">{error}</div>}{stats && stats.total === 0 && <div className="admin-state">No complaints have been submitted yet.</div>}{stats && <div className="stat-grid">{cards.map(([label, value]) => <article className="stat-card" key={label}><strong>{value}</strong><span>{label}</span></article>)}</div>}</section><p className="admin-disclaimer">These values are calculated from stored complaints. They are not AI categories, priorities, SLAs, or department-performance metrics.</p></>;
}

function ComplaintTable({ navigate, onExpired }: { navigate: (path: string) => void; onExpired: () => void }) {
  const [pageData, setPageData] = useState<AdminComplaintPage>(); const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ComplaintStatus | "">(""); const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState(""); const [photo, setPhoto] = useState("");
  const [location, setLocation] = useState(""); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setPageData(await listAdminComplaints({ page, pageSize: 10, status, query: submittedQuery, hasPhoto: photo === "yes" ? true : photo === "no" ? false : undefined, hasLocation: location === "yes" ? true : location === "no" ? false : undefined })); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Complaints could not be loaded."); } finally { setLoading(false); }
  }, [page, status, submittedQuery, photo, location, onExpired]);
  useEffect(() => { void load(); }, [load]);
  return <section className="admin-complaints" aria-labelledby="complaints-title"><div className="admin-title"><div><p className="eyebrow">Municipal queue</p><h1 id="complaints-title">Complaints</h1></div></div><form className="admin-filters" onSubmit={(event) => { event.preventDefault(); setPage(1); setSubmittedQuery(query); }} aria-label="Complaint filters"><label>Search<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ID, description, place or nearby details" /></label><label>Status<select value={status} onChange={(e) => { setStatus(e.target.value as ComplaintStatus | ""); setPage(1); }}><option value="">All statuses</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Photo<select value={photo} onChange={(e) => { setPhoto(e.target.value); setPage(1); }}><option value="">Any</option><option value="yes">With photo</option><option value="no">Without photo</option></select></label><label>Location<select value={location} onChange={(e) => { setLocation(e.target.value); setPage(1); }}><option value="">Any</option><option value="yes">With location</option><option value="no">Without location</option></select></label><div className="filter-actions"><button type="submit">Search</button><button type="button" onClick={() => { setQuery(""); setSubmittedQuery(""); setStatus(""); setPhoto(""); setLocation(""); setPage(1); }}>Clear</button></div></form>
    {loading && <div className="admin-state">Loading complaints…</div>}{error && <div className="admin-state admin-error" role="alert">{error}<button type="button" onClick={() => void load()}>Try again</button></div>}{!loading && !error && pageData?.items.length === 0 && <div className="admin-state">No complaints match these filters.</div>}{!loading && !error && pageData && pageData.items.length > 0 && <><div className="admin-table-wrap"><table><thead><tr><th>Complaint</th><th>Submitted</th><th>Location</th><th>Evidence</th><th>Status</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>{pageData.items.map((complaint) => <tr key={complaint.complaint_id}><td><strong>#{complaint.complaint_id.slice(0, 8)}</strong><span>{complaint.description}</span></td><td>{readableDate(complaint.created_at)}</td><td>{complaint.location_label ?? "Not provided"}</td><td>{complaint.image_ref ? "Photo" : "None"}</td><td><StatusPill status={complaint.status} /></td><td><AdminLink href={`/admin/complaints/${complaint.complaint_id}`} navigate={navigate}>Open</AdminLink></td></tr>)}</tbody></table></div><div className="pagination" aria-label="Complaint pages"><button disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button><span>Page {pageData.page} of {pageData.total_pages} · {pageData.total} complaints</span><button disabled={pageData.page >= pageData.total_pages} onClick={() => setPage((value) => value + 1)}>Next</button></div></>}
  </section>;
}

function ComplaintDetail({ complaintId, navigate, session, onExpired }: { complaintId: string; navigate: (path: string) => void; session: AuthSession; onExpired: () => void }) {
  const [complaint, setComplaint] = useState<Awaited<ReturnType<typeof getAdminComplaint>>>(); const [error, setError] = useState("");
  const [imageFailed, setImageFailed] = useState(false); const [target, setTarget] = useState<ComplaintStatus>();
  const [note, setNote] = useState(""); const [saving, setSaving] = useState(false); const [success, setSuccess] = useState("");
  const load = useCallback(async () => { setError(""); try { setComplaint(await getAdminComplaint(complaintId)); } catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Complaint could not be loaded."); } }, [complaintId, onExpired]);
  useEffect(() => { void load(); }, [load]); useEffect(() => { setTarget(undefined); setNote(""); setImageFailed(false); }, [complaintId]);
  async function submitStatus(event: FormEvent) { event.preventDefault(); if (!complaint || !target) return; setSaving(true); setError(""); setSuccess(""); try { await updateComplaintStatus(complaint.complaint_id, { newStatus: target, expectedUpdatedAt: complaint.updated_at, operatorNote: note }, session.csrf_token); await load(); setTarget(undefined); setNote(""); setSuccess("Status updated and recorded in history."); } catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Status could not be updated."); } finally { setSaving(false); } }
  if (error && !complaint) return <section className="admin-state admin-error" role="alert">{error}<button onClick={() => void load()}>Try again</button></section>;
  if (!complaint) return <div className="admin-state">Loading complaint…</div>; const hasCoordinates = complaint.latitude !== null && complaint.longitude !== null;
  return <section className="admin-detail"><AdminLink href="/admin/complaints" navigate={navigate} className="back-link">← Back to complaints</AdminLink><div className="detail-heading"><div><p className="eyebrow">Complaint #{complaint.complaint_id.slice(0, 8)}</p><h1>{complaint.description}</h1></div><StatusPill status={complaint.status} /></div>{error && <div className="admin-state admin-error" role="alert">{error}<button onClick={() => void load()}>Reload latest</button></div>}{success && <div className="admin-success" role="status">{success}</div>}<div className="detail-grid"><article className="detail-card"><h2>Complaint evidence</h2><dl><div><dt>Full reference</dt><dd>{complaint.complaint_id}</dd></div><div><dt>Submitted</dt><dd>{readableDate(complaint.created_at)}</dd></div></dl>{complaint.image_ref && !imageFailed ? <img src={imageUrl(complaint.image_ref)} alt="Citizen-submitted complaint evidence" onError={() => setImageFailed(true)} /> : <div className="evidence-placeholder">{imageFailed ? "Photo evidence could not be loaded." : "No photo evidence is stored."}</div>}</article><article className="detail-card"><h2>Issue location</h2><p className="location-label">{complaint.location_label ?? "No location was provided."}</p>{complaint.location_details && <p>{complaint.location_details}</p>}{complaint.location_precision && <p className="detail-muted">Precision: {complaint.location_precision} · Source: {complaint.location_source}</p>}{hasCoordinates ? <Suspense fallback={<div className="admin-state">Loading map…</div>}><ReadOnlyLocationMap latitude={complaint.latitude!} longitude={complaint.longitude!} readOnly /></Suspense> : <div className="evidence-placeholder">Map unavailable because this complaint has no coordinates.</div>}{hasCoordinates && <details><summary>Technical coordinates</summary><p>{complaint.latitude}, {complaint.longitude}</p></details>}</article></div><div className="detail-grid"><article className="detail-card"><h2>Update status</h2><form onSubmit={submitStatus}><label htmlFor="next-status">Next status</label><select id="next-status" value={target ?? ""} onChange={(e) => setTarget(e.target.value as ComplaintStatus)} required><option value="">Choose an allowed transition</option>{allowedTransitions[complaint.status].map((value) => <option key={value} value={value}>{statusLabels[value]}</option>)}</select><label htmlFor="operator-note">Internal operator note <span>Optional</span></label><textarea id="operator-note" value={note} onChange={(e) => setNote(e.target.value)} maxLength={1000} rows={4} placeholder="Example: Site inspected; repair crew notified" /><p className="detail-muted">Internal notes are visible only to authenticated municipal staff. This update records your account ID.</p><button type="submit" disabled={!target || saving}>{saving ? "Saving…" : "Record status change"}</button></form></article><article className="detail-card"><h2>Status history</h2><ol className="history-list">{complaint.history.map((event) => <li key={event.event_id}><span className="history-dot" /><div><strong>{event.event_type === "created" ? "Complaint submitted" : `${statusLabels[event.previous_status!]} → ${statusLabels[event.new_status]}`}</strong><time dateTime={event.occurred_at}>{readableDate(event.occurred_at)}</time>{event.actor_id && <small>Operator ID: {event.actor_id.slice(0, 8)}</small>}{event.operator_note && <p>{event.operator_note}</p>}</div></li>)}</ol></article></div></section>;
}

function UserManagement({ session, onExpired }: { session: AuthSession; onExpired: () => void }) {
  const [users, setUsers] = useState<MunicipalUser[]>([]); const [error, setError] = useState(""); const [username, setUsername] = useState(""); const [password, setPassword] = useState(""); const [role, setRole] = useState<MunicipalRole>("municipal_operator"); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => { try { setUsers(await listUsers()); setError(""); } catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Accounts could not be loaded."); } }, [onExpired]); useEffect(() => { void load(); }, [load]);
  async function submit(event: FormEvent) { event.preventDefault(); setSaving(true); setError(""); try { await createUser({ username, password, role }, session.csrf_token); setUsername(""); setPassword(""); setRole("municipal_operator"); await load(); } catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Account could not be created."); } finally { setSaving(false); } }
  async function change(user: MunicipalUser, input: { role?: MunicipalRole; is_active?: boolean }) { setError(""); try { await updateUser(user.user_id, input, session.csrf_token); await load(); } catch (reason) { if (reason instanceof ApiError && reason.status === 401) onExpired(); else setError(reason instanceof Error ? reason.message : "Account could not be updated."); } }
  return <section className="admin-users"><div className="admin-title"><div><p className="eyebrow">Administrator only</p><h1>Municipal accounts</h1></div></div>{error && <div className="admin-state admin-error" role="alert">{error}</div>}<div className="user-management-grid"><article className="detail-card"><h2>Create account</h2><form onSubmit={submit}><label htmlFor="new-username">Username</label><input id="new-username" value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} maxLength={64} required /><label htmlFor="new-password">Temporary password</label><input id="new-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} maxLength={128} required /><label htmlFor="new-role">Role</label><select id="new-role" value={role} onChange={(e) => setRole(e.target.value as MunicipalRole)}><option value="municipal_operator">Municipal operator</option><option value="municipal_admin">Municipal administrator</option></select><button disabled={saving}>{saving ? "Creating…" : "Create account"}</button></form><p className="detail-muted">Share credentials through a secure channel. Password reset is outside this milestone.</p></article><article className="detail-card account-list"><h2>Existing accounts</h2>{users.map((user) => <div className="account-row" key={user.user_id}><div><strong>{user.username}</strong><small>{roleLabels[user.role]} · {user.is_active ? "Active" : "Disabled"}</small></div><select aria-label={`Role for ${user.username}`} value={user.role} disabled={user.user_id === session.user.user_id} onChange={(e) => void change(user, { role: e.target.value as MunicipalRole })}><option value="municipal_operator">Operator</option><option value="municipal_admin">Administrator</option></select><button type="button" disabled={user.user_id === session.user.user_id} onClick={() => void change(user, { is_active: !user.is_active })}>{user.is_active ? "Disable" : "Reactivate"}</button></div>)}</article></div></section>;
}

export default function AdminApp() {
  const [path, navigate] = usePathname(); const [session, setSession] = useState<AuthSession>(); const [loading, setLoading] = useState(true); const [startupError, setStartupError] = useState(""); const intendedPath = path === "/admin/login" ? "/admin" : path;
  const verify = useCallback(async () => { setLoading(true); setStartupError(""); try { const current = await getSession(); setSession(current); if (window.location.pathname === "/admin/login") navigate("/admin"); } catch (reason) { setSession(undefined); if (!(reason instanceof ApiError && reason.status === 401)) setStartupError(reason instanceof Error ? reason.message : "Authentication service unavailable."); } finally { setLoading(false); } }, [navigate]);
  useEffect(() => { void verify(); }, [verify]); const expired = useCallback(() => { setSession(undefined); navigate("/admin/login"); }, [navigate]);
  if (loading) return <main className="admin-login-page"><div className="admin-state">Verifying municipal session…</div></main>;
  if (!session) return <><LoginPage returnTo={intendedPath} onAuthenticated={(nextSession, returnTo) => { setSession(nextSession); navigate(returnTo); }} />{startupError && <div className="admin-login-outage" role="alert">{startupError}</div>}</>;
  const match = path.match(/^\/admin\/complaints\/([^/]+)\/?$/); let content: ReactNode;
  if (path.startsWith("/admin/users")) content = session.user.role === "municipal_admin" ? <UserManagement session={session} onExpired={expired} /> : <section className="admin-state admin-error" role="alert">Administrator permission is required.</section>;
  else if (match) content = <ComplaintDetail complaintId={decodeURIComponent(match[1])} navigate={navigate} session={session} onExpired={expired} />;
  else if (path.startsWith("/admin/complaints")) content = <ComplaintTable navigate={navigate} onExpired={expired} />; else content = <Dashboard navigate={navigate} onExpired={expired} />;
  return <AdminShell navigate={navigate} session={session} onLogout={async () => { try { await logout(session.csrf_token); } finally { setSession(undefined); navigate("/admin/login"); } }}>{content}</AdminShell>;
}
