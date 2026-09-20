import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { Complaint, ComplaintInput, createComplaint, listComplaints, imageUrl } from "./api/complaints";

type FormFields = { description: string };
type FormErrors = { description?: string };
const initialFields: FormFields = { description: "" };
function validate(fields: FormFields): FormErrors {
  return fields.description.trim() ? {} : { description: "Tell us what needs attention." };
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
      {complaint.image_ref && <img className="evidence-image" src={imageUrl(complaint.image_ref)} alt="Photo attached to this complaint" loading="lazy" />}
      <div className="card-footer">
        <span className="reference">#{complaint.complaint_id.slice(0, 8)}</span>
        <span>{hasLocation ? "Location provided" : "Location not provided"}</span>
      </div>
    </article>
  );
}

export default function App() {
  const [fields, setFields] = useState<FormFields>(initialFields);
  const [errors, setErrors] = useState<FormErrors>({});
  const [image, setImage] = useState<File | undefined>();
  const [imageError, setImageError] = useState("");
  const imageInput = useRef<HTMLInputElement>(null);
  const [location, setLocation] = useState<{ latitude: number; longitude: number }>();
  const [locationMessage, setLocationMessage] = useState("Location is optional. You can submit without it.");
  const [locating, setLocating] = useState(false);
  const locationRequest = useRef(0);
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

  function chooseImage(file?: File) {
    setSuccessMessage("");
    setImage(undefined);
    setImageError("");
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setImageError("Choose a JPEG or PNG image.");
    } else if (file.size > 5 * 1024 * 1024) {
      setImageError("Image must be 5 MiB or smaller.");
    } else {
      setImage(file);
      return;
    }
    if (imageInput.current) imageInput.current.value = "";
  }

  function removeImage() {
    setImage(undefined);
    setImageError("");
    if (imageInput.current) imageInput.current.value = "";
  }

  function clearLocation() {
    locationRequest.current += 1;
    setLocation(undefined);
    setLocating(false);
    setLocationMessage("Location omitted. You can submit without it.");
  }

  function captureLocation() {
    const requestId = ++locationRequest.current;
    setLocation(undefined);
    if (!navigator.geolocation) {
      setLocationMessage("This browser does not support location. You can submit without it.");
      return;
    }
    setLocating(true);
    setLocationMessage("Finding your location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (requestId !== locationRequest.current) return;
        setLocating(false);
        const { latitude, longitude } = position.coords;
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) {
          setLocationMessage("Location could not be determined. You can submit without it.");
          return;
        }
        setLocation({ latitude, longitude });
        setLocationMessage("Location captured successfully");
      },
      (error) => {
        if (requestId !== locationRequest.current) return;
        setLocating(false);
        setLocationMessage(error.code === 1
          ? "Location permission denied. You can submit without it."
          : error.code === 3
            ? "Location request timed out. Try again or submit without it."
            : "Location could not be determined. You can submit without it.");
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 },
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(fields);
    setErrors(nextErrors);
    setSubmitError("");
    setSuccessMessage("");

    if (Object.keys(nextErrors).length > 0) return;

    const input: ComplaintInput = { description: fields.description.trim() };
    if (imageError) return;
    if (location) Object.assign(input, location);
    if (image) input.image = image;
    // Ignore any geolocation callback that arrives after submission begins.
    locationRequest.current += 1;
    setLocating(false);

    setIsSubmitting(true);
    try {
      const created = await createComplaint(input);
      setComplaints((current) => [created, ...current.filter((item) => item.complaint_id !== created.complaint_id)]);
      setFields(initialFields);
      setImage(undefined);
      if (imageInput.current) imageInput.current.value = "";
      setLocation(undefined);
      setLocationMessage("Location is optional. You can submit without it.");
      setListError("");
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
          <p className="hero-copy">Send a clear description of a local civic problem. Add a photo and your location if you wish, then submit your report.</p>
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

            <fieldset disabled={isSubmitting}>
              <legend>Photo evidence <span>Optional</span></legend>
              <label htmlFor="image">Attach a photo</label>
              <input ref={imageInput} id="image" type="file" accept="image/jpeg,image/png"
                onChange={(event) => chooseImage(event.target.files?.[0])} aria-describedby="image-help" />
              <p className="field-help" id="image-help">JPEG or PNG, up to 5 MiB. Avoid faces and private information.</p>
              {image && <p className="field-help">Selected: {image.name}</p>}
              {(image || imageError) && <button className="secondary-button" type="button" onClick={removeImage}>Remove image</button>}
              {imageError && <p className="field-error" role="alert">{imageError}</p>}
            </fieldset>

            <fieldset disabled={isSubmitting}>
              <legend>Where is the issue? <span>Optional</span></legend>
              <p className="field-help">Use this only while you are near the problem. Your browser will ask for permission.</p>
              <button className="secondary-button" type="button" onClick={captureLocation} disabled={locating}>Use my current location</button>
              {(location || locating) && <button className="secondary-button" type="button" onClick={clearLocation}>Continue without location</button>}
              <p className="field-help" aria-live="polite">{locationMessage}</p>
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
