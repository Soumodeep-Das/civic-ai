import { FormEvent, lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Complaint, ComplaintInput, createComplaint, imageUrl, listComplaints } from "./api/complaints";
import LocationPicker, { LocationSelection } from "./LocationPicker";
import { StatusBadge } from "./ui/StatusBadge";

const AdminApp = lazy(() => import("./admin/AdminApp"));

type FormFields = { description: string };
type FormErrors = { description?: string; image?: string; location?: string };
const initialFields: FormFields = { description: "" };

function validate(fields: FormFields): FormErrors {
  return fields.description.trim() ? {} : { description: "Tell us what needs attention." };
}

export function readableDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function useDocumentTitle(title: string) {
  useEffect(() => { document.title = title; }, [title]);
}

function EvidenceImage({ reference, alt }: { reference: string; alt: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) return <div className="image-fallback">Photo evidence could not be displayed.</div>;
  return <img className="evidence-image" src={imageUrl(reference)} alt={alt} loading="lazy" decoding="async" width="640" height="360" onError={() => setFailed(true)} />;
}

function ComplaintCard({ complaint }: { complaint: Complaint }) {
  const hasLocation = complaint.latitude !== null && complaint.longitude !== null;
  return <article className="complaint-card">
    <div className="card-meta"><StatusBadge status={complaint.status} /><time dateTime={complaint.created_at}>{readableDate(complaint.created_at)}</time></div>
    <p>{complaint.description}</p>
    {complaint.image_ref && <EvidenceImage reference={complaint.image_ref} alt="Complaint photo evidence" />}
    {complaint.location_label && <div className="complaint-location"><strong>{complaint.location_label}</strong><span>{complaint.location_precision === "exact" ? "Confirmed point" : complaint.location_precision === "broad" ? "Broad area" : "Approximate place"}</span>{complaint.location_details && <p>{complaint.location_details}</p>}</div>}
    <div className="card-footer"><span className="reference">Reference {complaint.complaint_id.slice(0, 8)}</span><span>{hasLocation ? "Location provided" : "Location not provided"}</span></div>
  </article>;
}

function ErrorSummary({ errors, summaryRef }: { errors: FormErrors; summaryRef: React.RefObject<HTMLDivElement | null> }) {
  const entries = [
    errors.description && { href: "#description", message: errors.description },
    errors.image && { href: "#image", message: errors.image },
    errors.location && { href: "#location-query", message: errors.location },
  ].filter(Boolean) as Array<{ href: string; message: string }>;
  if (!entries.length) return null;
  return <div className="error-summary" role="alert" tabIndex={-1} ref={summaryRef} aria-labelledby="error-summary-title"><h3 id="error-summary-title">There is a problem</h3><ul>{entries.map((entry) => <li key={entry.href}><a href={entry.href}>{entry.message}</a></li>)}</ul></div>;
}

function CitizenHeader() {
  return <header className="site-header"><a className="brand" href="/" aria-label="CivicAI citizen complaint service home"><span className="brand-mark" aria-hidden="true"><i /><i /><i /></span><span>Civic<span>AI</span></span></a><nav aria-label="Service navigation"><a href="#report-heading">Report an issue</a><a href="#complaints-heading">Recent complaints</a><a href="/admin">Municipal sign in</a></nav></header>;
}

function CitizenFooter() {
  return <footer><span>CivicAI · MCA academic project</span><span>Photos and locations are used as complaint evidence</span></footer>;
}

function CitizenApp() {
  useDocumentTitle("Report a civic issue | CivicAI");
  const [fields, setFields] = useState<FormFields>(initialFields);
  const [errors, setErrors] = useState<FormErrors>({});
  const [image, setImage] = useState<File | undefined>();
  const [imageError, setImageError] = useState("");
  const imageInput = useRef<HTMLInputElement>(null);
  const errorSummary = useRef<HTMLDivElement>(null);
  const [location, setLocation] = useState<LocationSelection>();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submittingRef = useRef(false);
  const [listError, setListError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [createdComplaint, setCreatedComplaint] = useState<Complaint>();

  const previewUrl = useMemo(() => !image || typeof URL.createObjectURL !== "function" ? "" : URL.createObjectURL(image), [image]);
  useEffect(() => () => { if (previewUrl && typeof URL.revokeObjectURL === "function") URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const hasMeaningfulDraft = Boolean(fields.description.trim() || image || location);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (hasMeaningfulDraft && !isSubmitting) event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [hasMeaningfulDraft, isSubmitting]);

  const loadComplaints = useCallback(async () => {
    setIsLoading(true); setListError("");
    try { setComplaints(await listComplaints()); }
    catch (error) { setListError(error instanceof Error ? error.message : "Recent complaints could not be loaded."); }
    finally { setIsLoading(false); }
  }, []);
  useEffect(() => { void loadComplaints(); }, [loadComplaints]);

  function updateDescription(value: string) {
    setFields({ description: value }); setErrors((current) => ({ ...current, description: undefined })); setCreatedComplaint(undefined);
  }

  function chooseImage(file?: File) {
    setCreatedComplaint(undefined); setImage(undefined); setImageError(""); setErrors((current) => ({ ...current, image: undefined }));
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type)) setImageError("Choose a JPEG or PNG image.");
    else if (file.size > 5 * 1024 * 1024) setImageError("Image must be 5 MiB or smaller.");
    else { setImage(file); return; }
    if (imageInput.current) imageInput.current.value = "";
  }

  function removeImage() {
    setImage(undefined); setImageError(""); setErrors((current) => ({ ...current, image: undefined }));
    if (imageInput.current) imageInput.current.value = "";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submittingRef.current) return;
    const nextErrors = validate(fields);
    if (!image) nextErrors.image = "Attach a JPEG or PNG photo of the issue.";
    if (!location?.confirmed) nextErrors.location = "Choose the issue location and confirm the selected point.";
    setErrors(nextErrors); setSubmitError(""); setCreatedComplaint(undefined);
    if (Object.keys(nextErrors).length > 0) { window.requestAnimationFrame(() => errorSummary.current?.focus()); return; }

    const input: ComplaintInput = { description: fields.description.trim(), image };
    if (location) Object.assign(input, { latitude: location.latitude, longitude: location.longitude, location_label: location.label, location_precision: location.precision, location_details: location.details.trim() || undefined, location_source: location.source, location_accuracy_m: location.accuracyMeters });
    submittingRef.current = true; setIsSubmitting(true);
    try {
      const created = await createComplaint(input);
      setComplaints((current) => [created, ...current.filter((item) => item.complaint_id !== created.complaint_id)]);
      setFields(initialFields); setImage(undefined); if (imageInput.current) imageInput.current.value = ""; setLocation(undefined); setListError(""); setErrors({}); setCreatedComplaint(created);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Your complaint could not be submitted. Your entries are still here; please try again.");
    } finally { submittingRef.current = false; setIsSubmitting(false); }
  }

  return <div className="citizen-app">
    <a className="skip-link" href="#main-content">Skip to main content</a><CitizenHeader />
    <main id="main-content">
      <section className="hero" aria-labelledby="page-title"><div><p className="eyebrow">CivicAI citizen service</p><h1 id="page-title">Report a civic issue</h1><p className="hero-copy">Tell the municipal team what happened, show the issue and confirm where it is. You can search for the place or use your current location.</p></div><div className="hero-assurance" aria-label="What you will need"><strong>Before you start</strong><span>A clear description</span><span>One photo</span><span>The issue location</span></div></section>
      <div className="workspace">
        <section className="form-panel" aria-labelledby="report-heading">
          <div className="section-heading"><div><span>Report an issue</span><h2 id="report-heading">Send complaint evidence</h2></div><p><span aria-hidden="true">*</span> Required fields</p></div>
          <form onSubmit={handleSubmit} noValidate>
            <ErrorSummary errors={errors} summaryRef={errorSummary} />
            <section className="form-step" aria-labelledby="description-heading"><div className="step-heading"><span aria-hidden="true">1</span><div><h3 id="description-heading">Describe the problem</h3><p>Say what is wrong and include a nearby landmark if helpful.</p></div></div><label htmlFor="description">What is happening? <span className="required-text">Required</span></label><textarea id="description" value={fields.description} onChange={(event) => updateDescription(event.target.value)} placeholder="Example: Large pothole beside the school entrance" rows={5} aria-invalid={Boolean(errors.description)} aria-describedby={errors.description ? "description-error" : "description-help"} />{errors.description ? <p className="field-error" id="description-error"><span className="sr-only">Error: </span>{errors.description}</p> : <p className="field-help" id="description-help">Do not include names, phone numbers or other private information.</p>}</section>
            <fieldset className="form-step" disabled={isSubmitting} aria-describedby={errors.image || imageError ? "image-error" : "image-help"}><legend><span className="step-number" aria-hidden="true">2</span><span><strong>Add photo evidence</strong><small>A clear photo helps staff identify the issue.</small></span></legend><label htmlFor="image">Attach a photo</label><span className="required-text">Required</span><input ref={imageInput} id="image" type="file" accept="image/jpeg,image/png" capture="environment" onChange={(event) => chooseImage(event.target.files?.[0])} aria-invalid={Boolean(errors.image || imageError)} /><p className="field-help" id="image-help">JPEG or PNG, up to 5 MiB. Avoid faces and private information.</p>{image && <div className="selected-image"><div className="image-preview">{previewUrl ? <img src={previewUrl} alt="Preview of selected complaint photo" /> : <span>Photo selected</span>}</div><div><strong>Selected: {image.name}</strong><button className="text-button" type="button" onClick={removeImage}>Remove image</button></div></div>}{imageError && <button className="secondary-button" type="button" onClick={removeImage}>Choose another photo</button>}{(imageError || errors.image) && <p className="field-error" id="image-error" role="alert"><span className="sr-only">Error: </span>{imageError || errors.image}</p>}</fieldset>
            <fieldset className="form-step" disabled={isSubmitting} aria-describedby={errors.location ? "location-error" : undefined}><legend><span className="step-number" aria-hidden="true">3</span><span><strong>Confirm where it happened</strong><small>Search for the issue location or use your device position if you are there now.</small></span></legend><LocationPicker value={location} error={errors.location} disabled={isSubmitting} onChange={(selection) => { setLocation(selection); setCreatedComplaint(undefined); if (selection?.confirmed) setErrors((current) => ({ ...current, location: undefined })); }} /></fieldset>
            <section className="form-step submit-step" aria-labelledby="submit-heading"><div className="step-heading"><span aria-hidden="true">4</span><div><h3 id="submit-heading">Review and submit</h3><p>Your photo and confirmed location will be stored as complaint evidence.</p></div></div>{submitError && <div className="notice error-notice" role="alert"><strong>Complaint not submitted</strong><p>{submitError}</p><p>Your description, photo and location have been kept on this page.</p></div>}{createdComplaint && <div className="success-panel" role="status" tabIndex={-1}><span className="success-icon" aria-hidden="true">✓</span><div><h3>Complaint submitted</h3><span className="sr-only">Complaint #{createdComplaint.complaint_id.slice(0, 8)} was submitted.</span><p>Your reference is <strong>{createdComplaint.complaint_id}</strong>.</p><p>Current status: <strong>Submitted</strong>. Municipal staff can now review the evidence. No response time is promised by this academic prototype.</p><a href="#report-heading">Report another issue</a></div></div>}<button className="primary-button" type="submit" disabled={isSubmitting} aria-describedby="submit-progress"><span>{isSubmitting ? "Submitting complaint…" : "Submit complaint"}</span><span aria-hidden="true">→</span></button><span className="sr-only" id="submit-progress" aria-live="polite">{isSubmitting ? "Submission in progress. Please wait." : ""}</span></section>
          </form>
        </section>
        <section className="list-panel" aria-labelledby="complaints-heading"><div className="section-heading list-heading"><div><span>Public status</span><h2 id="complaints-heading">Recent complaints</h2></div>{!isLoading && !listError && <span className="count" aria-label={`${complaints.length} complaints`}>{complaints.length}</span>}</div><p className="list-intro">Operational status is shown as text and colour. Internal municipal notes are never displayed here.</p><div className="complaint-list" aria-live="polite" aria-busy={isLoading}>{isLoading && <div className="state-card"><span className="spinner" aria-hidden="true" /><h3>Loading complaints</h3><p>Connecting to the complaint service.</p></div>}{!isLoading && listError && <div className="state-card error-state"><h3>Queue unavailable</h3><p>{listError}</p><button type="button" onClick={() => void loadComplaints()}>Try again</button></div>}{!isLoading && !listError && complaints.length === 0 && <div className="state-card"><span className="empty-icon" aria-hidden="true">✓</span><h3>No complaints yet</h3><p>The first submitted complaint will appear here.</p></div>}{!isLoading && !listError && complaints.map((complaint) => <ComplaintCard key={complaint.complaint_id} complaint={complaint} />)}</div></section>
      </div>
    </main><CitizenFooter />
  </div>;
}

function NotFoundPage() {
  useDocumentTitle("Page not found | CivicAI");
  return <div className="citizen-app"><a className="skip-link" href="#main-content">Skip to main content</a><CitizenHeader /><main id="main-content" className="route-state"><p className="eyebrow">Page not found</p><h1>We could not find that page</h1><p>Check the address or return to the citizen complaint service.</p><a className="primary-link" href="/">Go to CivicAI home</a></main><CitizenFooter /></div>;
}

function RouteLoader() { return <main className="route-loader" id="main-content" role="status"><span className="spinner" aria-hidden="true" /><p>Loading municipal workspace…</p></main>; }

export default function App() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  if (path.startsWith("/admin")) return <Suspense fallback={<RouteLoader />}><AdminApp /></Suspense>;
  return path === "/" ? <CitizenApp /> : <NotFoundPage />;
}
