import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../App";

vi.mock("../LocationMap", () => ({
  default: ({ readOnly }: { readOnly?: boolean }) => <div>Mock {readOnly ? "read-only" : "editable"} map</div>,
}));

const complaint = {
  complaint_id: "58c6a21d-e82c-4ee2-88aa-e56d86a14ce5",
  image_ref: "/api/v1/complaint-images/demo.png",
  description: "Large pothole near the school entrance",
  latitude: 22.5726,
  longitude: 88.3639,
  location_label: "School entrance, Kolkata, West Bengal",
  location_precision: "exact",
  location_details: "Beside the main gate",
  location_source: "map",
  location_accuracy_m: null,
  status: "submitted",
  created_at: "2026-09-29T08:00:00Z",
  updated_at: "2026-09-29T08:00:00Z",
};

const createdEvent = {
  event_id: "3ab084bd-67ad-441a-942a-c97653ded2be",
  complaint_id: complaint.complaint_id,
  event_type: "created",
  previous_status: null,
  new_status: "submitted",
  operator_note: null,
  actor_id: null,
  occurred_at: complaint.created_at,
};

const authSession = {
  user: { user_id: "a1248a87-580b-4b37-849a-55c380499998", username: "ward.operator", role: "municipal_operator", is_active: true, created_at: "2026-09-30T08:00:00Z", updated_at: "2026-09-30T08:00:00Z", last_login_at: "2026-09-30T08:01:00Z" },
  csrf_token: "test-csrf-token", expires_at: "2026-09-30T16:00:00Z",
};

function json(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

function installAdminApi(options: { empty?: boolean; fail?: boolean } = {}) {
  let current = { ...complaint };
  let history: Array<Record<string, unknown>> = [createdEvent];
  return vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.endsWith("/api/v1/auth/me")) return json(authSession);
    if (options.fail) return Promise.reject(new TypeError("offline"));
    if (url.endsWith("/api/v1/admin/dashboard")) return json({
      total: options.empty ? 0 : 1, submitted: options.empty ? 0 : 1, under_review: 0,
      in_progress: 0, resolved: 0, rejected: 0,
      submitted_last_7_days: options.empty ? 0 : 1, with_photo: options.empty ? 0 : 1,
      with_location: options.empty ? 0 : 1,
    });
    if (url.endsWith(`/api/v1/admin/complaints/${complaint.complaint_id}/status`) && init?.method === "PATCH") {
      current = { ...current, status: "under_review", updated_at: "2026-09-29T09:00:00Z" };
      history = [...history, {
        ...createdEvent, event_id: "5b9fceec-262e-4fd8-a6bd-69f0c904cbbd",
        event_type: "status_changed", previous_status: "submitted", new_status: "under_review",
        operator_note: "Site inspection requested", occurred_at: current.updated_at,
      }];
      return json(current);
    }
    if (url.endsWith(`/api/v1/admin/complaints/${complaint.complaint_id}`)) return json({ ...current, history });
    if (url.includes("/api/v1/admin/complaints?")) return json({
      items: options.empty ? [] : [current], page: 1, page_size: 10,
      total: options.empty ? 0 : 1, total_pages: options.empty ? 0 : 1,
    });
    return Promise.reject(new Error(`Unexpected request ${url}`));
  });
}

beforeEach(() => {
  window.history.replaceState({}, "", "/admin");
  Object.defineProperty(window, "scrollTo", { configurable: true, value: vi.fn() });
});

afterEach(() => window.history.replaceState({}, "", "/"));

test("loads real dashboard statistics in an authenticated shell", async () => {
  installAdminApi();
  render(<App />);
  expect(await screen.findByText("Total complaints")).toBeInTheDocument();
  expect(screen.getAllByText("1").length).toBeGreaterThan(0);
  expect(screen.getByText("ward.operator")).toBeInTheDocument();
  expect(screen.getByText(/not AI categories/)).toBeInTheDocument();
});

test("shows an empty dashboard", async () => {
  installAdminApi({ empty: true });
  render(<App />);
  expect(await screen.findByText("No complaints have been submitted yet.")).toBeInTheDocument();
});

test("loads complaint table and sends accessible filters", async () => {
  const fetchMock = installAdminApi();
  const user = userEvent.setup();
  window.history.replaceState({}, "", "/admin/complaints");
  render(<App />);
  expect(await screen.findByText(complaint.description)).toBeInTheDocument();
  await user.type(screen.getByLabelText("Search"), "school gate");
  await user.selectOptions(screen.getByLabelText("Status"), "submitted");
  await user.selectOptions(screen.getByLabelText("Photo"), "yes");
  await user.click(screen.getByRole("button", { name: "Search" }));
  await waitFor(() => expect(fetchMock.mock.calls.some(([value]) => {
    const url = String(value);
    return url.includes("q=school+gate") && url.includes("status=submitted") && url.includes("has_photo=true");
  })).toBe(true));
  expect(screen.getByText("Page 1 of 1 · 1 complaints")).toBeInTheDocument();
});

test("shows zero-result filters", async () => {
  installAdminApi({ empty: true });
  window.history.replaceState({}, "", "/admin/complaints");
  render(<App />);
  expect(await screen.findByText("No complaints match these filters.")).toBeInTheDocument();
});

test("shows API failure with retry", async () => {
  installAdminApi({ fail: true });
  window.history.replaceState({}, "", "/admin/complaints");
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent("could not be reached");
  expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
});

test("detail shows evidence, read-only map and status history", async () => {
  installAdminApi();
  window.history.replaceState({}, "", `/admin/complaints/${complaint.complaint_id}`);
  render(<App />);
  expect(await screen.findByText(complaint.description)).toBeInTheDocument();
  expect(screen.getByAltText("Citizen-submitted complaint evidence")).toHaveAttribute("src", complaint.image_ref);
  expect(await screen.findByText("Mock read-only map")).toBeInTheDocument();
  expect(screen.getByText("Complaint submitted")).toBeInTheDocument();
  expect(screen.getByText("Technical coordinates")).toBeInTheDocument();
});

test("records a controlled status update and refreshes history", async () => {
  const fetchMock = installAdminApi();
  const user = userEvent.setup();
  window.history.replaceState({}, "", `/admin/complaints/${complaint.complaint_id}`);
  render(<App />);
  await screen.findByText("Complaint submitted");
  await user.selectOptions(screen.getByLabelText("Next status"), "under_review");
  await user.type(screen.getByLabelText(/Internal operator note/), "Site inspection requested");
  await user.click(screen.getByRole("button", { name: "Record status change" }));
  expect(await screen.findByText("Status updated and recorded in history.")).toBeInTheDocument();
  expect(screen.getByText("Submitted → Under review")).toBeInTheDocument();
  const request = fetchMock.mock.calls.find(([value, init]) => String(value).endsWith("/status") && init?.method === "PATCH");
  expect(JSON.parse(String(request?.[1]?.body))).toEqual({
    new_status: "under_review", expected_updated_at: complaint.updated_at,
    operator_note: "Site inspection requested",
  });
});

test("handles missing image and missing map without breaking detail", async () => {
  const noLocation = { ...complaint, image_ref: null, latitude: null, longitude: null, location_label: null, location_precision: null, location_details: null, location_source: null };
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    if (String(input).endsWith("/api/v1/auth/me")) return json(authSession);
    if (String(input).endsWith(`/api/v1/admin/complaints/${complaint.complaint_id}`)) return json({ ...noLocation, history: [createdEvent] });
    return Promise.reject(new Error("Unexpected request"));
  });
  window.history.replaceState({}, "", `/admin/complaints/${complaint.complaint_id}`);
  render(<App />);
  expect(await screen.findByText("No photo evidence is stored.")).toBeInTheDocument();
  expect(screen.getByText("Map unavailable because this complaint has no coordinates.")).toBeInTheDocument();
});

test("handles an image load failure", async () => {
  installAdminApi();
  const user = userEvent.setup();
  window.history.replaceState({}, "", `/admin/complaints/${complaint.complaint_id}`);
  render(<App />);
  const image = await screen.findByAltText("Citizen-submitted complaint evidence");
  await user.click(image);
  image.dispatchEvent(new Event("error"));
  expect(await screen.findByText("Photo evidence could not be loaded.")).toBeInTheDocument();
});

test("blocks an unauthenticated admin route and signs in safely", async () => {
  let authenticated = false;
  vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.endsWith("/api/v1/auth/me")) return authenticated ? json(authSession) : json({ message: "Authentication required." }, 401);
    if (url.endsWith("/api/v1/auth/login") && init?.method === "POST") { authenticated = true; return json(authSession); }
    if (url.endsWith("/api/v1/admin/dashboard")) return json({ total: 0, submitted: 0, under_review: 0, in_progress: 0, resolved: 0, rejected: 0, submitted_last_7_days: 0, with_photo: 0, with_location: 0 });
    return Promise.reject(new Error(`Unexpected request ${url}`));
  });
  const user = userEvent.setup();
  window.history.replaceState({}, "", "/admin"); render(<App />);
  expect(await screen.findByRole("heading", { name: "Municipal sign in" })).toBeInTheDocument();
  await user.type(screen.getByLabelText("Username"), "ward.operator");
  await user.type(screen.getByLabelText("Password"), "demo-password-value");
  await user.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByRole("heading", { name: "Operations dashboard" })).toBeInTheDocument();
});

test("shows a generic login error", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    if (String(input).endsWith("/api/v1/auth/me")) return json({ message: "Authentication required." }, 401);
    if (String(input).endsWith("/api/v1/auth/login")) return json({ message: "Invalid username or password." }, 401);
    return Promise.reject(new Error("Unexpected request"));
  });
  const user = userEvent.setup(); render(<App />); await screen.findByText("Municipal sign in");
  await user.type(screen.getByLabelText("Username"), "unknown.user");
  await user.type(screen.getByLabelText("Password"), "wrong-password");
  await user.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Invalid username or password.");
});

test("logout invalidates frontend state and sends the CSRF token", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/auth/me")) return json(authSession);
    if (url.endsWith("/api/v1/admin/dashboard")) return json({ total: 0, submitted: 0, under_review: 0, in_progress: 0, resolved: 0, rejected: 0, submitted_last_7_days: 0, with_photo: 0, with_location: 0 });
    if (url.endsWith("/api/v1/auth/logout")) return Promise.resolve(new Response(null, { status: 204 }));
    return Promise.reject(new Error("Unexpected request"));
  });
  const user = userEvent.setup(); render(<App />); await screen.findByText("ward.operator");
  await user.click(screen.getByRole("button", { name: "Sign out" }));
  expect(await screen.findByText("Municipal sign in")).toBeInTheDocument();
  const call = fetchMock.mock.calls.find(([value]) => String(value).endsWith("/api/v1/auth/logout"));
  expect(new Headers(call?.[1]?.headers).get("X-CSRF-Token")).toBe("test-csrf-token");
});

test("operator cannot open administrator account controls", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/api/v1/auth/me") ? json(authSession) : Promise.reject(new Error("Unexpected request")));
  window.history.replaceState({}, "", "/admin/users"); render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Administrator permission is required.");
  expect(screen.queryByText("Accounts")).not.toBeInTheDocument();
});

test("an expired session during protected loading returns to login", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/auth/me")) return json(authSession);
    if (url.endsWith("/api/v1/admin/dashboard")) return json({ message: "Authentication required." }, 401);
    return Promise.reject(new Error(`Unexpected request ${url}`));
  });
  window.history.replaceState({}, "", "/admin"); render(<App />);
  expect(await screen.findByRole("heading", { name: "Municipal sign in" })).toBeInTheDocument();
  expect(window.location.pathname).toBe("/admin/login");
});

test("administrator sees and manages municipal accounts", async () => {
  const adminSession = { ...authSession, user: { ...authSession.user, role: "municipal_admin" } };
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/auth/me")) return json(adminSession);
    if (url.endsWith("/api/v1/admin/users")) return json([adminSession.user]);
    return Promise.reject(new Error(`Unexpected request ${url}`));
  });
  window.history.replaceState({}, "", "/admin/users"); render(<App />);
  expect(await screen.findByRole("heading", { name: "Municipal accounts" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Create account" })).toBeInTheDocument();
  expect(screen.getByText("Accounts")).toBeInTheDocument();
});
