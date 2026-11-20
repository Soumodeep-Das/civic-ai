import { useEffect, useState } from "react";
type Entry = { event_id: string; kind: string; created_at: string; note: string; context?: Record<string, string>; decision?: string; corrected_band?: string; suggestion?: { state: string; band: string | null; reasons: string[]; unknowns: string[]; emergency_review: boolean } };
const questions = { immediate_danger: "Immediate danger reported?", access_blocked: "Public access blocked?", essential_service_interrupted: "Essential service interrupted?" };
export function PriorityPanel({ complaintId, csrf }: { complaintId: string; csrf: string }) {
  const [events, setEvents] = useState<Entry[]>([]);
  const [facts, setFacts] = useState<Record<string, string>>({ immediate_danger: "unknown", access_blocked: "unknown", essential_service_interrupted: "unknown" });
  const [source, setSource] = useState("municipal_report");
  const [note, setNote] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [band, setBand] = useState("Medium");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const base = `/api/v1/admin/complaints/${complaintId}/priority`;
  async function request(path = "", body?: object) {
    const r = await fetch(base + path, body ? { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify(body) } : { credentials: "same-origin" });
    if (!r.ok) throw new Error(r.status === 409 ? "Context changed. Reload before reviewing." : "Priority action failed. Reload and check your session before retrying.");
    return r.json();
  }
  useEffect(() => { let active = true; request().then(data => { if (active) setEvents(data); }).catch(e => { if (active) setError(e.message); }); return () => { active = false; }; }, [base]);
  async function submit(path: string, body: object) {
    setBusy(true); setError("");
    try { await request(path, body); setEvents(await request()); } catch (e) { setError(e instanceof Error ? e.message : "Priority unavailable"); } finally { setBusy(false); }
  }
  const latest = events.filter(e => e.kind === "context").at(-1);
  const suggestion = latest?.suggestion;
  return <article className="detail-card"><h2>Experimental contextual priority</h2><p>Reported facts, not verified findings. This rules-based prototype does not assess photos or dispatch emergency assistance. Every suggestion requires staff review.</p>
    {error && <p role="alert">{error}</p>}
    <fieldset disabled={busy}><legend>Record reported context</legend><label>Information source<select value={source} onChange={e => setSource(e.target.value)}><option value="municipal_report">Municipal staff report</option><option value="citizen_report">Citizen report transcribed by staff</option></select></label>
    {Object.entries(questions).map(([key, label]) => <label key={key}>{label}<select value={facts[key]} onChange={e => setFacts({ ...facts, [key]: e.target.value })}>{["unknown", "yes", "no", "conflict"].map(v => <option key={v} value={v}>{v}</option>)}</select></label>)}
    <label>Context evidence explanation<textarea maxLength={1000} value={note} onChange={e => setNote(e.target.value)} /></label><button type="button" disabled={!note.trim()} onClick={() => void submit("/context", { context: { source, ...facts }, note })}>Save context and suggest priority</button></fieldset>
    {suggestion && <><h3>{suggestion.band ? `Suggested priority: ${suggestion.band}` : "Needs municipal review"}</h3>{suggestion.emergency_review && <p role="alert">Reported potential immediate danger: escalate through the appropriate emergency process. This portal does not dispatch assistance.</p>}<p>{suggestion.reasons.map(r => r.replaceAll("_", " ")).join("; ")}</p><p>Unknown facts: {suggestion.unknowns.join(", ") || "none reported"}</p><fieldset disabled={busy}><legend>Review priority</legend><label>Priority review explanation<textarea maxLength={1000} value={reviewNote} onChange={e => setReviewNote(e.target.value)} /></label>{["accepted", "deferred", "corrected"].map(decision => <button type="button" key={decision} disabled={!reviewNote.trim() || (decision === "accepted" && suggestion.state !== "suggested")} onClick={() => void submit("/reviews", { snapshot_id: latest!.event_id, decision, note: reviewNote, ...(decision === "corrected" ? { corrected_band: band } : {}) })}>{decision === "accepted" ? "Accept priority" : decision === "deferred" ? "Defer priority" : "Save priority correction"}</button>)}<label>Corrected priority<select value={band} onChange={e => setBand(e.target.value)}>{["Low", "Medium", "High", "Critical"].map(v => <option key={v}>{v}</option>)}</select></label></fieldset></>}
    <h3>Priority history</h3><p>Saved decisions do not change complaint status or assignment.</p><ol>{events.map(e => <li key={e.event_id}>{e.kind === "context" ? "Context recorded" : e.decision}{e.corrected_band && `: ${e.corrected_band}`} — {new Date(e.created_at).toLocaleString()}<p>{e.note}</p>{e.context && <dl>{Object.entries(e.context).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{value.replaceAll("_", " ")}</dd></div>)}</dl>}</li>)}</ol>
  </article>;
}
