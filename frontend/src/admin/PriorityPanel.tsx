import { useEffect, useState } from "react";

type Entry = { event_id: string; kind: string; created_at: string; note: string; context?: Record<string, string>; decision?: string; corrected_band?: string; suggestion?: { state: string; band: string | null; reasons: string[]; unknowns: string[]; emergency_review: boolean } };
const questions = { immediate_danger: "Immediate danger reported?", access_blocked: "Public access blocked?", essential_service_interrupted: "Essential service interrupted?" };
const display = (value: string) => value.replaceAll("_", " ");

export function PriorityPanel({ complaintId, csrf }: { complaintId: string; csrf: string }) {
  const [events, setEvents] = useState<Entry[]>([]);
  const [facts, setFacts] = useState<Record<string, string>>({ immediate_danger: "unknown", access_blocked: "unknown", essential_service_interrupted: "unknown" });
  const [source, setSource] = useState("municipal_report");
  const [note, setNote] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [band, setBand] = useState("Medium");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const base = `/api/v1/admin/complaints/${complaintId}/priority`;

  async function request(path = "", body?: object) {
    const response = await fetch(base + path, body ? { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify(body) } : { credentials: "same-origin" }).catch(error => {
      if (body) throw new Error("Save outcome unknown. Reload the complaint and check its history before retrying.");
      throw error;
    });
    if (!response.ok) throw new Error(response.status === 409 ? "Context changed. Reload before reviewing." : "Priority action failed. Reload and check your session before retrying.");
    return response.json();
  }

  useEffect(() => { let active = true; request().then(data => { if (active) setEvents(data); }).catch(error => { if (active) setError(error.message); }); return () => { active = false; }; }, [base]);
  async function submit(path: string, body: object) {
    setBusy(true); setError(""); setMessage("");
    try { await request(path, body); setMessage("Saved."); setReviewNote(""); setNote(""); try { setEvents(await request()); } catch { setError("Saved, but history could not refresh. Reload the complaint before taking another action."); } }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Priority unavailable"); }
    finally { setBusy(false); }
  }

  const latest = events.filter(event => event.kind === "context").at(-1);
  const suggestion = latest?.suggestion;
  return <article className="detail-card decision-panel priority-panel">
    <header className="decision-header"><span className="decision-icon" aria-hidden="true">P</span><div><p className="panel-kicker">Decision support</p><h2>Contextual priority</h2><p>Reported impact is assessed by transparent rules. Staff confirmation is required.</p></div><span className="experimental-tag">Experimental</span></header>
    <div className="decision-boundary"><strong>Scope</strong><span>Reported context only</span><span>No photo assessment</span><span>No emergency dispatch</span></div>
    {message && <p className="inline-feedback success" role="status">{message}</p>}{error && <p className="inline-feedback error" role="alert">{error}</p>}
    <fieldset className="decision-section" disabled={busy}><legend><span>1</span> Record context</legend><div className="decision-form-grid"><label className="wide-field">Information source<select value={source} onChange={event => setSource(event.target.value)}><option value="municipal_report">Municipal staff report</option><option value="citizen_report">Citizen report transcribed by staff</option></select></label>{Object.entries(questions).map(([key, label]) => <label key={key}>{label}<select value={facts[key]} onChange={event => setFacts({ ...facts, [key]: event.target.value })}>{["unknown", "yes", "no", "conflict"].map(value => <option key={value} value={value}>{display(value)}</option>)}</select></label>)}</div><label>Context evidence explanation<textarea maxLength={1000} value={note} onChange={event => setNote(event.target.value)} placeholder="Record what was reported and how it was checked." /></label><button className="decision-primary" type="button" disabled={!note.trim()} onClick={() => void submit("/context", { context: { source, ...facts }, note })}>Save context and suggest priority</button></fieldset>
    {suggestion && <section className="suggestion-card" aria-labelledby="priority-suggestion-title"><div className="suggestion-title"><div><p className="panel-kicker">Current suggestion</p><h3 id="priority-suggestion-title">{suggestion.band ?? "Municipal review needed"}</h3></div><span className={`decision-badge ${suggestion.state}`}>{display(suggestion.state)}</span></div>{suggestion.emergency_review && <p className="emergency-callout" role="alert"><strong>Potential immediate danger reported.</strong> Follow the appropriate emergency process. CivicAI does not dispatch assistance.</p>}<dl className="suggestion-facts"><div><dt>Why</dt><dd>{suggestion.reasons.map(display).join("; ")}</dd></div><div><dt>Unknown</dt><dd>{suggestion.unknowns.map(display).join(", ") || "None reported"}</dd></div></dl><fieldset className="review-box" disabled={busy}><legend><span>2</span> Review decision</legend><label>Review explanation<textarea maxLength={1000} value={reviewNote} onChange={event => setReviewNote(event.target.value)} placeholder="Explain the evidence behind your decision." /></label><div className="review-correction"><label>Correction value<select value={band} onChange={event => setBand(event.target.value)}>{["Low", "Medium", "High", "Critical"].map(value => <option key={value}>{value}</option>)}</select></label><button className="decision-secondary" type="button" disabled={!reviewNote.trim()} onClick={() => void submit("/reviews", { snapshot_id: latest!.event_id, decision: "corrected", note: reviewNote, corrected_band: band })}>Save correction</button></div><div className="decision-actions"><button className="decision-primary" type="button" disabled={!reviewNote.trim() || suggestion.state !== "suggested"} onClick={() => void submit("/reviews", { snapshot_id: latest!.event_id, decision: "accepted", note: reviewNote })}>Accept priority</button><button className="decision-tertiary" type="button" disabled={!reviewNote.trim()} onClick={() => void submit("/reviews", { snapshot_id: latest!.event_id, decision: "deferred", note: reviewNote })}>Defer for review</button></div></fieldset></section>}
    <section className="decision-history"><div className="history-heading"><div><p className="panel-kicker">Audit trail</p><h3>Priority history</h3></div><span>{events.length} {events.length === 1 ? "event" : "events"}</span></div><p>Saved decisions do not change complaint status or assignment.</p>{events.length === 0 ? <p className="empty-state">No priority activity recorded.</p> : <ol>{events.map(event => <li key={event.event_id}><div className="history-marker" aria-hidden="true" /><div><div className="history-event-title"><strong>{event.kind === "context" ? "Context recorded" : display(event.decision ?? "review")}{event.corrected_band && ` · ${event.corrected_band}`}</strong><time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time></div><p>{event.note}</p>{event.context && <dl>{Object.entries(event.context).map(([key, value]) => <div key={key}><dt>{display(key)}</dt><dd>{display(value)}</dd></div>)}</dl>}</div></li>)}</ol>}</section>
  </article>;
}
