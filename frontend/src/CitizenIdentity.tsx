import { FormEvent, useEffect, useRef, useState } from "react";

import { ApiError } from "./api/complaints";
import {
  CitizenSession, OwnedComplaint, changePassword, citizenLogin, citizenLogout, citizenSignup,
  forgotPassword, getCitizenSession, getMyComplaint, listMyComplaints, resetPassword,
  verifyCitizenEmail,
} from "./api/citizenAuth";
import { CitizenFooter, CitizenHeader, readableDate } from "./App";
import { StatusBadge } from "./ui/StatusBadge";

function message(reason: unknown, fallback: string) { return reason instanceof Error ? reason.message : fallback; }
function title(value: string) { document.title = `${value} | CivicAI`; }

function AuthLayout({ children }: { children: React.ReactNode }) {
  return <div className="citizen-app"><a className="skip-link" href="#main-content">Skip to main content</a><CitizenHeader /><main id="main-content" className="identity-page">{children}</main><CitizenFooter /></div>;
}

function FieldError({ children }: { children?: string }) { return children ? <p className="field-error" role="alert">{children}</p> : null; }

function SignIn() {
  title("Sign in"); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const googleError = new URLSearchParams(location.search).get("google_error");
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(""); try { await citizenLogin(email, password); location.assign("/my-complaints"); } catch (reason) { setError(message(reason, "Sign in failed.")); setBusy(false); } }
  return <AuthLayout><section className="identity-card"><p className="eyebrow">Citizen account</p><h1>Welcome back</h1><p>Sign in to see complaints submitted through your account.</p>{(error || googleError) && <div className="notice error-notice" role="alert">{error || "Google sign-in could not be completed. Try again or use your password."}</div>}<a className="google-button" href="/api/v1/citizen-auth/google/start">Continue with Google</a><div className="identity-divider"><span>or</span></div><form onSubmit={submit}><label htmlFor="email">Email</label><input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /><label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /><a className="form-side-link" href="/forgot-password">Forgot password?</a><button className="primary-button" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button></form><p>Don&apos;t have an account? <a href="/sign-up">Create account</a></p></section></AuthLayout>;
}

function SignUp() {
  title("Create account"); const summary = useRef<HTMLDivElement>(null); const [name, setName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [confirm, setConfirm] = useState(""); const [error, setError] = useState(""); const [done, setDone] = useState(false); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); if (password !== confirm) { setError("Passwords do not match."); requestAnimationFrame(() => summary.current?.focus()); return; } setBusy(true); setError(""); try { await citizenSignup({ display_name: name, email, password }); setDone(true); } catch (reason) { setError(message(reason, "Account could not be created.")); requestAnimationFrame(() => summary.current?.focus()); } finally { setBusy(false); } }
  return <AuthLayout><section className="identity-card"><p className="eyebrow">Citizen account</p><h1>Create your CivicAI account</h1>{done ? <div className="success-panel" role="status"><div><h2>Check your email</h2><p>Use the single-use verification link before signing in.</p><a href="/sign-in">Return to sign in</a></div></div> : <><a className="google-button" href="/api/v1/citizen-auth/google/start">Continue with Google</a><div className="identity-divider"><span>or</span></div>{error && <div className="error-summary" role="alert" tabIndex={-1} ref={summary}><h2>There is a problem</h2><p>{error}</p></div>}<form onSubmit={submit} noValidate><label htmlFor="name">Name</label><input id="name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} maxLength={100} required /><label htmlFor="email">Email</label><input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /><label htmlFor="new-password">Password</label><input id="new-password" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={15} maxLength={128} required /><p className="field-help">Use at least 15 characters. Spaces and passphrases are welcome.</p><label htmlFor="confirm-password">Confirm password</label><input id="confirm-password" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required /><button className="primary-button" disabled={busy}>{busy ? "Creating account…" : "Create account"}</button></form></>}<p>Already have an account? <a href="/sign-in">Sign in</a></p></section></AuthLayout>;
}

function VerifyEmail() {
  title("Verify email"); const token = new URLSearchParams(location.search).get("token") ?? ""; const [state, setState] = useState("Verifying your email…"); const [ok, setOk] = useState(false);
  useEffect(() => { if (!token) { setState("This verification link is incomplete."); return; } void verifyCitizenEmail(token).then((result) => { setState(result.message); setOk(true); }).catch((reason) => setState(message(reason, "This link is invalid or expired."))); }, [token]);
  return <AuthLayout><section className="identity-card"><h1>{ok ? "Email verified" : "Verify email"}</h1><div className={ok ? "notice success-notice" : "notice"} role="status">{state}</div>{ok && <a className="primary-link" href="/sign-in">Sign in</a>}</section></AuthLayout>;
}

function ForgotPassword() {
  title("Forgot password"); const [email, setEmail] = useState(""); const [done, setDone] = useState(false); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); try { await forgotPassword(email); setDone(true); } finally { setBusy(false); } }
  return <AuthLayout><section className="identity-card"><h1>Reset your password</h1>{done ? <div className="notice success-notice" role="status">If an account exists for that email, a reset link has been sent.</div> : <form onSubmit={submit}><label htmlFor="email">Email</label><input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /><button className="primary-button" disabled={busy}>Send reset link</button></form>}</section></AuthLayout>;
}

function ResetPassword() {
  title("Reset password"); const token = new URLSearchParams(location.search).get("token") ?? ""; const [password, setPassword] = useState(""); const [confirm, setConfirm] = useState(""); const [error, setError] = useState(""); const [done, setDone] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); if (password !== confirm) { setError("Passwords do not match."); return; } try { await resetPassword(token, password); setDone(true); } catch (reason) { setError(message(reason, "This reset link is invalid or expired.")); } }
  return <AuthLayout><section className="identity-card"><h1>Choose a new password</h1>{done ? <div className="success-panel" role="status"><div><h2>Password reset</h2><a href="/sign-in">Sign in</a></div></div> : <form onSubmit={submit}><FieldError>{error}</FieldError><label htmlFor="password">New password</label><input id="password" type="password" autoComplete="new-password" minLength={15} maxLength={128} value={password} onChange={(e) => setPassword(e.target.value)} required /><label htmlFor="confirm">Confirm password</label><input id="confirm" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required /><button className="primary-button">Reset password</button></form>}</section></AuthLayout>;
}

function AccountLayout({ session, children }: { session: CitizenSession; children: React.ReactNode }) { return <div className="citizen-app"><a className="skip-link" href="#main-content">Skip to main content</a><CitizenHeader accountName={session.account.display_name} /><main id="main-content" className="account-page">{children}</main><CitizenFooter /></div>; }

function MyComplaints({ session }: { session: CitizenSession }) {
  title("My complaints"); const [items, setItems] = useState<OwnedComplaint[]>(); const [error, setError] = useState("");
  useEffect(() => { void listMyComplaints().then((page) => setItems(page.items)).catch((reason) => setError(message(reason, "Complaints could not be loaded."))); }, []);
  return <AccountLayout session={session}><p className="eyebrow">Citizen account</p><h1>My Complaints</h1><p>Only complaints submitted while signed in—or securely claimed with a private tracking link—appear here.</p>{error && <div className="notice error-notice" role="alert">{error}</div>}{!items && !error && <p role="status">Loading your complaints…</p>}{items?.length === 0 && <div className="state-card"><h2>No saved complaints</h2><p>Submit a report while signed in to save it here.</p><a href="/">Report an issue</a></div>}<div className="complaint-list">{items?.map((item) => <article className="complaint-card" key={item.complaint_id}><div className="card-meta"><StatusBadge status={item.status} /><time>{readableDate(item.created_at)}</time></div><p>{item.description}</p><a href={`/complaints/${item.complaint_id}`}>View complaint</a></article>)}</div></AccountLayout>;
}

function ComplaintDetail({ session, id }: { session: CitizenSession; id: string }) {
  title("Complaint details"); const [item, setItem] = useState<OwnedComplaint>(); const [error, setError] = useState("");
  useEffect(() => { void getMyComplaint(id).then(setItem).catch((reason) => setError(message(reason, "Complaint not found."))); }, [id]);
  return <AccountLayout session={session}><a href="/my-complaints">← My Complaints</a><h1>Complaint details</h1>{error && <div className="notice error-notice" role="alert">{error}</div>}{item && <><article className="detail-card"><StatusBadge status={item.status} /><h2>{item.description}</h2><p>Reference {item.complaint_id}</p>{item.location_label && <p><strong>Submitted location:</strong> {item.location_label}</p>}{item.image_ref && <img src={item.image_ref} alt="Evidence submitted with this complaint" />}</article><section className="detail-card"><h2>Status history</h2><ol className="status-timeline">{item.history.map((event, index) => <li key={`${event.occurred_at}-${index}`}><strong>{event.new_status.replaceAll("_", " ")}</strong><time>{readableDate(event.occurred_at)}</time></li>)}</ol></section></>}</AccountLayout>;
}

function Profile({ session }: { session: CitizenSession }) {
  title("Profile and security"); const [current, setCurrent] = useState(""); const [next, setNext] = useState(""); const [confirm, setConfirm] = useState(""); const [feedback, setFeedback] = useState("");
  async function change(event: FormEvent) { event.preventDefault(); if (next !== confirm) { setFeedback("New passwords do not match."); return; } try { setFeedback((await changePassword(current, next, session.csrf_token)).message); setCurrent(""); setNext(""); setConfirm(""); } catch (reason) { setFeedback(message(reason, "Password could not be changed.")); } }
  return <AccountLayout session={session}><p className="eyebrow">Citizen account</p><h1>Profile and security</h1><section className="detail-card"><h2>{session.account.display_name}</h2><p>{session.account.email}</p><p>Email verified · Google {session.account.google_connected ? "connected" : "not connected"}</p>{!session.account.google_connected && <p className="detail-muted">For safety, an existing password account is never linked to Google merely because the email matches. Explicit linking is deferred.</p>}</section>{session.account.has_password ? <section className="detail-card"><h2>Change password</h2>{feedback && <div className="notice" role="status">{feedback}</div>}<form onSubmit={change}><label htmlFor="current">Current password</label><input id="current" type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} required /><label htmlFor="next">New password</label><input id="next" type="password" autoComplete="new-password" minLength={15} value={next} onChange={(e) => setNext(e.target.value)} required /><label htmlFor="confirm">Confirm new password</label><input id="confirm" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required /><button className="primary-action">Change password</button></form></section> : <section className="detail-card"><h2>Password</h2><p>This Google-only account has no CivicAI password. A secure set-password flow is deferred.</p></section>}<button className="secondary-button" onClick={() => void citizenLogout(session.csrf_token).finally(() => location.assign("/sign-in"))}>Sign out</button></AccountLayout>;
}

export default function CitizenIdentity() {
  const path = location.pathname.replace(/\/$/, "") || "/"; const [session, setSession] = useState<CitizenSession>(); const [checked, setChecked] = useState(false);
  useEffect(() => { void getCitizenSession().then(setSession).catch((reason) => { if (!(reason instanceof ApiError && reason.status === 401)) console.error("Citizen session check failed"); }).finally(() => setChecked(true)); }, []);
  if (["/sign-in", "/sign-up", "/verify-email", "/forgot-password", "/reset-password"].includes(path)) {
    if (path === "/sign-in") return <SignIn />; if (path === "/sign-up") return <SignUp />; if (path === "/verify-email") return <VerifyEmail />; if (path === "/forgot-password") return <ForgotPassword />; return <ResetPassword />;
  }
  if (!checked) return <AuthLayout><p role="status">Loading your account…</p></AuthLayout>;
  if (!session) { location.replace(`/sign-in?return_to=${encodeURIComponent(location.pathname)}`); return null; }
  if (path === "/my-complaints") return <MyComplaints session={session} />;
  if (path === "/profile") return <Profile session={session} />;
  const match = path.match(/^\/complaints\/([^/]+)$/); if (match) return <ComplaintDetail session={session} id={decodeURIComponent(match[1])} />;
  return <AuthLayout><h1>Page not found</h1><a href="/my-complaints">Go to My Complaints</a></AuthLayout>;
}
