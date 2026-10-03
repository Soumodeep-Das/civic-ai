import { FormEvent, useState } from "react";

import { acceptStaffInvitation } from "./api/auth";

export default function StaffAcceptInvite() {
  document.title = "Accept staff invitation | CivicAI";
  const token = new URLSearchParams(location.search).get("token") ?? "";
  const [name, setName] = useState(""); const [username, setUsername] = useState("");
  const [password, setPassword] = useState(""); const [confirm, setConfirm] = useState("");
  const [error, setError] = useState(""); const [done, setDone] = useState(false); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirm) { setError("Passwords do not match."); return; }
    setBusy(true); setError("");
    try { await acceptStaffInvitation({ token, display_name: name, username, password }); setDone(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Invitation could not be accepted."); }
    finally { setBusy(false); }
  }
  return <div className="admin-login-page"><main id="main-content" className="admin-login-card"><a href="/" className="admin-brand">Civic<span>AI</span> Operations</a><p className="eyebrow">Approved municipal access</p><h1>Accept staff invitation</h1>{done ? <div className="admin-notice" role="status"><strong>Account activated</strong><p>Your administrator-selected role and departments are ready.</p><a href="/staff/sign-in">Continue to municipal staff sign in</a></div> : <form onSubmit={submit}>{error && <div className="admin-state admin-error" role="alert">{error}</div>}<label htmlFor="staff-name">Display name</label><input id="staff-name" autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} required /><label htmlFor="staff-username">Username</label><input id="staff-username" autoComplete="username" minLength={3} maxLength={64} pattern="[a-z0-9._-]+" value={username} onChange={(event) => setUsername(event.target.value.toLowerCase())} required /><label htmlFor="staff-password">Password</label><input id="staff-password" type="password" autoComplete="new-password" minLength={12} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} required /><label htmlFor="staff-confirm">Confirm password</label><input id="staff-confirm" type="password" autoComplete="new-password" value={confirm} onChange={(event) => setConfirm(event.target.value)} required /><button disabled={busy}>{busy ? "Activating account…" : "Activate municipal account"}</button></form>}<p>Role and department access are controlled by the inviting administrator.</p></main></div>;
}
