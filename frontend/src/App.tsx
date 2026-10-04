import { FormEvent, lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";

import { CitizenComplaintStatus, ComplaintInput, ComplaintSubmission, createComplaint, getComplaintStatus } from "./api/complaints";
import LocationPicker, { LocationSelection } from "./LocationPicker";
import { StatusBadge } from "./ui/StatusBadge";
import { CitizenSession, getCitizenSession } from "./api/citizenAuth";

const AdminApp = lazy(() => import("./admin/AdminApp"));
const CitizenIdentity = lazy(() => import("./CitizenIdentity"));
const StaffAcceptInvite = lazy(() => import("./StaffAcceptInvite"));

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

function ErrorSummary({ errors, summaryRef }: { errors: FormErrors; summaryRef: React.RefObject<HTMLDivElement | null> }) {
  const entries = [
    errors.description && { href: "#description", message: errors.description },
    errors.image && { href: "#image", message: errors.image },
    errors.location && { href: "#location-query", message: errors.location },
  ].filter(Boolean) as Array<{ href: string; message: string }>;
  if (!entries.length) return null;
  return <div className="error-summary" role="alert" tabIndex={-1} ref={summaryRef} aria-labelledby="error-summary-title"><h3 id="error-summary-title">There is a problem</h3><ul>{entries.map((entry) => <li key={entry.href}><a href={entry.href}>{entry.message}</a></li>)}</ul></div>;
}

export function CitizenHeader({ accountName }: { accountName?: string } = {}) {
  return <><header className="site-header"><a className="brand" href="/" aria-label="CivicAI citizen complaint service home"><span className="brand-mark" aria-hidden="true"><i /><i /><i /></span><span>Civic<span>AI</span></span></a><nav aria-label="Service navigation"><a href="/#report-heading">Report Issue</a><a href="/track">Track complaint</a>{accountName ? <><a href="/my-complaints">My Complaints</a><a href="/profile">Profile<span className="sr-only"> for {accountName}</span></a></> : <><a href="/sign-in">Sign in</a><a href="/sign-up">Create account</a></>}<a href="/staff/sign-in">Municipal staff</a></nav></header>{import.meta.env.VITE_CLOSED_BETA === "true" && <div className="beta-banner" role="status"><strong>Closed beta</strong> — test data may be reset; please avoid personal or sensitive information.</div>}</>;
}

export function CitizenFooter() {
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submittingRef = useRef(false);
  const [submitError, setSubmitError] = useState("");
  const [createdComplaint, setCreatedComplaint] = useState<ComplaintSubmission>();
  const [citizenSession, setCitizenSession] = useState<CitizenSession>();
  useEffect(() => { void getCitizenSession().then(setCitizenSession).catch(() => undefined); }, []);

  const previewUrl = useMemo(() => !image || typeof URL.createObjectURL !== "function" ? "" : URL.createObjectURL(image), [image]);
  useEffect(() => () => { if (previewUrl && typeof URL.revokeObjectURL === "function") URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const hasMeaningfulDraft = Boolean(fields.description.trim() || image || location);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (hasMeaningfulDraft && !isSubmitting) event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [hasMeaningfulDraft, isSubmitting]);

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
      setFields(initialFields); setImage(undefined); if (imageInput.current) imageInput.current.value = ""; setLocation(undefined); setErrors({}); setCreatedComplaint(created);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Your complaint could not be submitted. Your entries are still here; please try again.");
    } finally { submittingRef.current = false; setIsSubmitting(false); }
  }

  return <div className="citizen-app">
    <a className="skip-link" href="#main-content">Skip to main content</a><CitizenHeader accountName={citizenSession?.account.display_name} />
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
            <section className="form-step submit-step" aria-labelledby="submit-heading"><div className="step-heading"><span aria-hidden="true">4</span><div><h3 id="submit-heading">Review and submit</h3><p>Your photo and confirmed location will be stored as protected complaint evidence.</p></div></div>{!citizenSession && <p className="field-help">You can report without an account. <a href="/sign-in">Sign in</a> first if you want this complaint saved in My Complaints.</p>}{submitError && <div className="notice error-notice" role="alert"><strong>Complaint not submitted</strong><p>{submitError}</p><p>Your description, photo and location have been kept on this page.</p></div>}{createdComplaint && <div className="success-panel" role="status" tabIndex={-1}><span className="success-icon" aria-hidden="true">✓</span><div><h3>Complaint submitted</h3><span className="sr-only">Complaint #{createdComplaint.complaint_id.slice(0, 8)} was submitted.</span><p>Your reference is <strong>{createdComplaint.complaint_id}</strong>.</p><p>Current status: <strong>Submitted</strong>. Evidence is visible only to authorized municipal staff.</p>{citizenSession && <><a href={`/complaints/${createdComplaint.complaint_id}`}>View in My Complaints</a><br /></>}<a href={`/track/${createdComplaint.complaint_id}?token=${createdComplaint.tracking_token}`}>Open and save your private status link</a><br /><a href="#report-heading">Report another issue</a></div></div>}<button className="primary-button" type="submit" disabled={isSubmitting} aria-describedby="submit-progress"><span>{isSubmitting ? "Submitting complaint…" : "Submit complaint"}</span><span aria-hidden="true">→</span></button><span className="sr-only" id="submit-progress" aria-live="polite">{isSubmitting ? "Submission in progress. Please wait." : ""}</span></section>
          </form>
        </section>
        <aside className="list-panel" aria-labelledby="privacy-heading"><div className="section-heading list-heading"><div><span>Evidence privacy</span><h2 id="privacy-heading">Your report is not a public post</h2></div></div><p className="list-intro">Descriptions, exact locations and photos are not published in a global complaint feed. After submission, save the private status link shown in your receipt.</p><div className="state-card"><h3>Municipal access only</h3><p>Authorized staff can inspect the evidence and update the complaint. A tracking link shows only its reference, description, timestamps and status.</p></div></aside>
      </div>
    </main><CitizenFooter />
  </div>;
}

function TrackingPage() {
  useDocumentTitle("Track complaint | CivicAI");
  const complaintId = window.location.pathname.split("/")[2] ?? "";
  const token = new URLSearchParams(window.location.search).get("token") ?? "";
  const [complaint, setComplaint] = useState<CitizenComplaintStatus>();
  const [error, setError] = useState("");
  useEffect(() => { void getComplaintStatus(complaintId, token).then(setComplaint).catch(() => setError("This tracking link is invalid or no longer available.")); }, [complaintId, token]);
  return <div className="citizen-app"><a className="skip-link" href="#main-content">Skip to main content</a><CitizenHeader /><main id="main-content" className="route-state"><p className="eyebrow">Private complaint tracking</p><h1>Complaint status</h1>{error && <div className="notice error-notice" role="alert"><strong>Status unavailable</strong><p>{error}</p></div>}{!error && !complaint && <p role="status">Loading complaint status…</p>}{complaint && <article className="complaint-card"><div className="card-meta"><StatusBadge status={complaint.status} /><time dateTime={complaint.updated_at}>Updated {readableDate(complaint.updated_at)}</time></div><p>{complaint.description}</p><div className="card-footer"><span className="reference">Reference {complaint.complaint_id}</span></div></article>}<p>Photos, precise location and internal municipal activity are deliberately not displayed here.</p><a className="primary-link" href="/">Return to CivicAI home</a></main><CitizenFooter /></div>;
}

function TrackingLookupPage() {
  useDocumentTitle("Track a complaint | CivicAI");
  const [reference, setReference] = useState("");
  const [token, setToken] = useState("");
  function submit(event: FormEvent) {
    event.preventDefault();
    if (reference.trim() && token.trim()) window.location.assign(`/track/${encodeURIComponent(reference.trim())}?token=${encodeURIComponent(token.trim())}`);
  }
  return <div className="citizen-app"><CitizenHeader /><main id="main-content" className="route-state"><p className="eyebrow">Private complaint tracking</p><h1>Track a complaint</h1><p>Use the reference and private tracking token from your submission receipt.</p><form onSubmit={submit}><label htmlFor="tracking-reference">Complaint reference</label><input id="tracking-reference" required value={reference} onChange={(event) => setReference(event.target.value)} /><label htmlFor="tracking-token">Private tracking token</label><input id="tracking-token" required value={token} onChange={(event) => setToken(event.target.value)} /><button className="primary-button" type="submit">View status</button></form></main><CitizenFooter /></div>;
}

function NotFoundPage() {
  useDocumentTitle("Page not found | CivicAI");
  return <div className="citizen-app"><a className="skip-link" href="#main-content">Skip to main content</a><CitizenHeader /><main id="main-content" className="route-state"><p className="eyebrow">Page not found</p><h1>We could not find that page</h1><p>Check the address or return to the citizen complaint service.</p><a className="primary-link" href="/">Go to CivicAI home</a></main><CitizenFooter /></div>;
}

function RouteLoader() { return <main className="route-loader" id="main-content" role="status"><span className="spinner" aria-hidden="true" /><p>Loading municipal workspace…</p></main>; }

export default function App() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  if (path === "/staff/accept-invite") return <Suspense fallback={<RouteLoader />}><StaffAcceptInvite /></Suspense>;
  if (path.startsWith("/admin") || path.startsWith("/municipal") || path.startsWith("/staff/")) return <Suspense fallback={<RouteLoader />}><AdminApp /></Suspense>;
  if (path.startsWith("/track/")) return <TrackingPage />;
  if (path === "/track") return <TrackingLookupPage />;
  if (["/sign-in", "/sign-up", "/verify-email", "/forgot-password", "/reset-password", "/my-complaints", "/profile"].includes(path) || path.startsWith("/complaints/")) return <Suspense fallback={<RouteLoader />}><CitizenIdentity /></Suspense>;
  return path === "/" ? <CitizenApp /> : <NotFoundPage />;
}
