import { useEffect, useState } from "react";

type Assessment = { assessment_id: string; state: string; suggested_family: string | null; reasons: string[] };
type Review = { review_id: string; decision: string; note: string; corrected_family?: string };
const families = ["solid_waste", "roads_and_pedestrian_access", "drainage_and_sewerage", "public_lighting"];
const display = (value: string) => value.replaceAll("_", " ");

export function AssessmentPanel({ complaintId, csrf }: { complaintId: string; csrf: string }) {
  const [items, setItems] = useState<Assessment[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [note, setNote] = useState("");
  const [family, setFamily] = useState("solid_waste");
  const [history, setHistory] = useState<Review[]>([]);
  const base = `/api/v1/admin/complaints/${complaintId}/assessments`;

  async function request(url: string, body?: object) {
    const response = await fetch(url, body === undefined ? { credentials: "same-origin" } : { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify(body) }).catch(error => {
      if (body) throw new Error("Save outcome unknown. Reload the complaint and check its history before retrying.");
      throw error;
    });
    if (!response.ok) throw new Error(response.status === 503 ? "Experimental model is not configured or unavailable. Normal complaint handling remains available." : "Assessment action failed. Check your session and reload before trying again.");
    return response.json();
  }

  useEffect(() => { let active = true; setItems([]); setError(""); setMessage(""); request(base).then(data => { if (active) setItems(data); }).catch(error => { if (active) setError(error.message); }); return () => { active = false; }; }, [base]);
  useEffect(() => { let active = true; setHistory([]); const item = items[0]; if (item) request(`${base}/${item.assessment_id}/reviews`).then(data => { if (active) setHistory(data); }).catch(error => { if (active) setError(error.message); }); return () => { active = false; }; }, [base, items]);

  async function generate() {
    setBusy(true); setError("");
    try { await request(base, {}); try { setItems(await request(base)); } catch { setError("Assessment saved. Reload the complaint to see the updated history."); } }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Assessment unavailable"); }
    finally { setBusy(false); }
  }
  async function review(item: Assessment, decision: string) {
    setBusy(true); setError("");
    try { await request(`${base}/${item.assessment_id}/reviews`, { decision, note, ...(decision === "corrected" ? { corrected_family: family } : {}) }); setMessage("Review saved. Complaint status and priority were not changed."); setNote(""); try { setHistory(await request(`${base}/${item.assessment_id}/reviews`)); } catch { setError("Review saved. Reload the complaint to see the updated history."); } }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Review failed"); }
    finally { setBusy(false); }
  }

  return <article className="detail-card decision-panel assessment-panel">
    <header className="decision-header"><span className="decision-icon" aria-hidden="true">C</span><div><p className="panel-kicker">Decision support</p><h2>Text classification</h2><p>A small Bengaluru text experiment proposes one supported civic family for staff review.</p></div><span className="experimental-tag">Experimental</span></header>
    <div className="decision-boundary"><strong>Scope</strong><span>Complaint description</span><span>Four supported families</span><span>Human review required</span></div>
    {error && <p className="inline-feedback error" role="alert">{error}</p>}{message && <p className="inline-feedback success" role="status">{message}</p>}
    <div className="generate-row"><div><strong>Generate a new assessment</strong><span>The result is stored separately from workflow status.</span></div><button className="decision-primary" type="button" disabled={busy} onClick={() => void generate()}>{busy ? "Working…" : "Generate experimental assessment"}</button></div>
    {!items.length && <div className="empty-state"><strong>No assessment yet</strong><span>Generate one to create a reviewable category suggestion.</span></div>}
    {items.slice(0, 1).map(item => <section className="suggestion-card" key={item.assessment_id}><div className="suggestion-title"><div><p className="panel-kicker">Current suggestion</p><h3>{item.suggested_family ? display(item.suggested_family) : "Municipal review needed"}</h3></div><span className={`decision-badge ${item.state}`}>{display(item.state)}</span></div><dl className="suggestion-facts"><div><dt>Reason</dt><dd>{item.reasons.map(display).join("; ")}</dd></div></dl><div className="review-box"><h4><span>1</span> Record review</h4><label>Review explanation<textarea value={note} maxLength={1000} onChange={event => setNote(event.target.value)} placeholder="Explain what you checked before deciding." /></label><div className="review-correction"><label>Correct category<select value={family} onChange={event => setFamily(event.target.value)}>{families.map(value => <option key={value} value={value}>{display(value)}</option>)}</select></label><button className="decision-secondary" type="button" disabled={busy || !note.trim()} onClick={() => void review(item, "corrected")}>Save correction</button></div><div className="decision-actions"><button className="decision-primary" type="button" disabled={busy || !note.trim() || item.state !== "suggested"} onClick={() => void review(item, "accepted")}>Accept suggestion</button><button className="decision-tertiary" type="button" disabled={busy || !note.trim()} onClick={() => void review(item, "deferred")}>Defer for review</button></div></div><section className="decision-history compact"><div className="history-heading"><div><p className="panel-kicker">Audit trail</p><h4>Review history</h4></div><span>{history.length} {history.length === 1 ? "review" : "reviews"}</span></div>{history.length === 0 ? <p className="empty-state">No reviews recorded.</p> : <ol>{history.map(entry => <li key={entry.review_id}><div className="history-marker" aria-hidden="true" /><div><strong>{display(entry.decision)}{entry.corrected_family && ` · ${display(entry.corrected_family)}`}</strong><p>{entry.note}</p></div></li>)}</ol>}</section></section>)}
  </article>;
}
