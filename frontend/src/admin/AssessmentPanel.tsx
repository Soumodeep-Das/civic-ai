import { useEffect, useState } from "react";

type Assessment = { assessment_id: string; state: string; suggested_family: string | null; reasons: string[] };
export function AssessmentPanel({ complaintId, csrf }: { complaintId: string; csrf: string }) {
  const [items, setItems] = useState<Assessment[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [note, setNote] = useState("");
  const [family, setFamily] = useState("solid_waste");
  const [history, setHistory] = useState<{ review_id: string; decision: string; note: string; corrected_family?: string }[]>([]);
  const base = `/api/v1/admin/complaints/${complaintId}/assessments`;
  async function request(url: string, body?: object) {
    const response = await fetch(url, body === undefined ? { credentials: "same-origin" } : { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(response.status === 503 ? "Experimental model is not configured or unavailable. Normal complaint handling remains available." : "Assessment action failed. Check your session and reload before trying again.");
    return response.json();
  }
  useEffect(() => { let active = true; setItems([]); setError(""); setMessage("");
    request(base).then(data => { if (active) setItems(data); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [base]);
  useEffect(() => { let active = true; setHistory([]); const item = items[0];
    if (item) request(`${base}/${item.assessment_id}/reviews`).then(data => { if (active) setHistory(data); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [base, items]);
  async function generate() { setBusy(true); setError(""); try { await request(base, {}); setItems(await request(base)); } catch (e) { setError(e instanceof Error ? e.message : "Assessment unavailable"); } finally { setBusy(false); } }
  async function review(item: Assessment, decision: string) { setBusy(true); setError(""); try { await request(`${base}/${item.assessment_id}/reviews`, { decision, note, ...(decision === "corrected" ? { corrected_family: family } : {}) }); setMessage("Review saved. Complaint status and priority were not changed."); setNote(""); setHistory(await request(`${base}/${item.assessment_id}/reviews`)); } catch (e) { setError(e instanceof Error ? e.message : "Review failed"); } finally { setBusy(false); } }
  return <article className="detail-card"><h2>Experimental text assessment</h2><p>Trained on a small Bengaluru sample with AI-proposed labels. Suggestions require staff review; photos and urgency are not assessed.</p>
    {error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    <button type="button" disabled={busy} onClick={() => void generate()}>{busy ? "Working…" : "Generate experimental assessment"}</button>
    {!items.length && <p>No stored assessment loaded.</p>}
    {items.slice(0, 1).map(item => <div key={item.assessment_id}><h3>{item.suggested_family?.replaceAll("_", " ") ?? "Needs municipal review"}</h3><p>{item.reasons.map(r => r.replaceAll("_", " ")).join("; ")}</p><label>Review explanation<textarea value={note} maxLength={1000} onChange={e => setNote(e.target.value)} /></label><button type="button" disabled={busy || !note.trim() || item.state !== "suggested"} onClick={() => void review(item, "accepted")}>Accept suggestion</button><button type="button" disabled={busy || !note.trim()} onClick={() => void review(item, "deferred")}>Defer for review</button><label>Correct category<select value={family} onChange={e => setFamily(e.target.value)}>{["solid_waste", "roads_and_pedestrian_access", "drainage_and_sewerage", "public_lighting"].map(value => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label><button type="button" disabled={busy || !note.trim()} onClick={() => void review(item, "corrected")}>Save correction</button><h4>Review history</h4>{history.length === 0 ? <p>No reviews loaded.</p> : <ol>{history.map(entry => <li key={entry.review_id}><strong>{entry.decision}</strong>{entry.corrected_family && `: ${entry.corrected_family.replaceAll("_", " ")}`}<p>{entry.note}</p></li>)}</ol>}</div>)}
  </article>;
}
