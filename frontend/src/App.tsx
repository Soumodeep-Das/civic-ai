import { FormEvent, useCallback, useEffect, useState } from "react";

import { Complaint, ComplaintInput, createComplaint, listComplaints } from "./api/complaints";

type FormFields = {
  description: string;
  latitude: string;
  longitude: string;
};

type FormErrors = Partial<Record<keyof FormFields, string>>;

const initialFields: FormFields = { description: "", latitude: "", longitude: "" };

function coordinateValue(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  return Number(value);
}

function validate(fields: FormFields): FormErrors {
  const errors: FormErrors = {};
  const latitude = coordinateValue(fields.latitude);
  const longitude = coordinateValue(fields.longitude);

  if (!fields.description.trim()) errors.description = "Tell us what needs attention.";
  if (latitude !== undefined && (!Number.isFinite(latitude) || latitude < -90 || latitude > 90)) {
    errors.latitude = "Latitude must be between -90 and 90.";
  }
  if (longitude !== undefined && (!Number.isFinite(longitude) || longitude < -180 || longitude > 180)) {
    errors.longitude = "Longitude must be between -180 and 180.";
  }

  return errors;
}

function readableDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function ComplaintCard({ complaint }: { complaint: Complaint }) {
  const hasLocation = complaint.latitude !== null || complaint.longitude !== null;

  return (
    <article className="complaint-card">
      <div className="card-meta">
        <span className="status-pill"><span aria-hidden="true" />{complaint.status}</span>
        <time dateTime={complaint.created_at}>{readableDate(complaint.created_at)}</time>
      </div>
      <p>{complaint.description}</p>
      <div className="card-footer">
        <span className="reference">#{complaint.complaint_id.slice(0, 8)}</span>
        <span>{hasLocation ? `${complaint.latitude ?? "—"}, ${complaint.longitude ?? "—"}` : "Location not provided"}</span>
      </div>
    </article>
  );
}

export default function App() {
  const [fields, setFields] = useState<FormFields>(initialFields);
  const [errors, setErrors] = useState<FormErrors>({});
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [listError, setListError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadComplaints = useCallback(async () => {
    setIsLoading(true);
    setListError("");
    try {
      setComplaints(await listComplaints());
    } catch (error) {
      setListError(error instanceof Error ? error.message : "Complaints could not be loaded.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadComplaints();
  }, [loadComplaints]);

  function updateField(field: keyof FormFields, value: string) {
    setFields((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setSuccessMessage("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(fields);
    setErrors(nextErrors);
    setSubmitError("");
    setSuccessMessage("");

    if (Object.keys(nextErrors).length > 0) return;

    const input: ComplaintInput = { description: fields.description.trim() };
    const latitude = coordinateValue(fields.latitude);
    const longitude = coordinateValue(fields.longitude);
    if (latitude !== undefined) input.latitude = latitude;
    if (longitude !== undefined) input.longitude = longitude;

    setIsSubmitting(true);
    try {
      const created = await createComplaint(input);
      setComplaints((current) => [created, ...current.filter((item) => item.complaint_id !== created.complaint_id)]);
      setFields(initialFields);
      setSuccessMessage(`Complaint #${created.complaint_id.slice(0, 8)} was submitted.`);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "The complaint could not be submitted.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="CivicAI home">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>Civic<span>AI</span></span>
        </a>
        <span className="header-label">Community complaint desk</span>
      </header>

      <section className="hero" id="top">
        <div>
          <p className="eyebrow">Your street. Your voice.</p>
          <h1>Report what needs<br /><em>attention.</em></h1>
          <p className="hero-copy">Send a clear description of a local civic problem. Your report is stored in the project database and added to the complaint queue.</p>
        </div>
        <div className="hero-number" aria-hidden="true">01</div>
      </section>

      <div className="workspace">
        <section className="form-panel" aria-labelledby="report-heading">
          <div className="section-heading">
            <div><span>Step 01</span><h2 id="report-heading">Describe the issue</h2></div>
            <p>Fields marked required must be completed.</p>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <label htmlFor="description">What is happening? <strong>*</strong></label>
            <textarea
              id="description"
              value={fields.description}
              onChange={(event) => updateField("description", event.target.value)}
              placeholder="Example: Large pothole near the school entrance"
              rows={5}
              aria-invalid={Boolean(errors.description)}
              aria-describedby={errors.description ? "description-error" : "description-help"}
            />
            {errors.description ? <p className="field-error" id="description-error">{errors.description}</p> : <p className="field-help" id="description-help">Include a landmark or nearby building when useful.</p>}

            <fieldset>
              <legend>Location coordinates <span>Optional</span></legend>
              <div className="coordinate-grid">
                <div>
                  <label htmlFor="latitude">Latitude</label>
                  <input id="latitude" inputMode="decimal" value={fields.latitude} onChange={(event) => updateField("latitude", event.target.value)} placeholder="22.5726" aria-invalid={Boolean(errors.latitude)} aria-describedby={errors.latitude ? "latitude-error" : undefined} />
                  {errors.latitude && <p className="field-error" id="latitude-error">{errors.latitude}</p>}
                </div>
                <div>
                  <label htmlFor="longitude">Longitude</label>
                  <input id="longitude" inputMode="decimal" value={fields.longitude} onChange={(event) => updateField("longitude", event.target.value)} placeholder="88.3639" aria-invalid={Boolean(errors.longitude)} aria-describedby={errors.longitude ? "longitude-error" : undefined} />
                  {errors.longitude && <p className="field-error" id="longitude-error">{errors.longitude}</p>}
                </div>
              </div>
            </fieldset>

            {submitError && <div className="notice error-notice" role="alert">{submitError}</div>}
            {successMessage && <div className="notice success-notice" role="status">{successMessage}</div>}

            <button className="primary-button" type="submit" disabled={isSubmitting}>
              <span>{isSubmitting ? "Submitting…" : "Submit complaint"}</span>
              <span aria-hidden="true">↗</span>
            </button>
          </form>
        </section>

        <section className="list-panel" aria-labelledby="complaints-heading">
          <div className="section-heading list-heading">
            <div><span>Live queue</span><h2 id="complaints-heading">Recent complaints</h2></div>
            {!isLoading && !listError && <span className="count" aria-label={`${complaints.length} complaints`}>{complaints.length}</span>}
          </div>

          <div className="complaint-list" aria-live="polite">
            {isLoading && <div className="state-card"><span className="spinner" aria-hidden="true" /><h3>Loading complaints</h3><p>Connecting to the local complaint service.</p></div>}
            {!isLoading && listError && <div className="state-card error-state"><h3>Queue unavailable</h3><p>{listError}</p><button type="button" onClick={() => void loadComplaints()}>Try again</button></div>}
            {!isLoading && !listError && complaints.length === 0 && <div className="state-card"><span className="empty-icon" aria-hidden="true">✓</span><h3>No complaints yet</h3><p>New reports will appear here after submission.</p></div>}
            {!isLoading && !listError && complaints.map((complaint) => <ComplaintCard key={complaint.complaint_id} complaint={complaint} />)}
          </div>
        </section>
      </div>

      <footer><span>CivicAI · MCA project prototype</span><span>Anonymous local demonstration</span></footer>
    </main>
  );
}
