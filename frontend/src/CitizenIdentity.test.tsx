import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";

import App from "./App";

const json = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
const session = {
  account: { account_id: "citizen-1", display_name: "Civic Citizen", email: "citizen@example.com", state: "active", email_verified_at: "2026-10-03T00:00:00Z", google_connected: false, has_password: true },
  csrf_token: "citizen-csrf", expires_at: "2026-10-03T08:00:00Z",
};

beforeEach(() => { vi.restoreAllMocks(); window.history.replaceState({}, "", "/"); });

test("citizen creates an account with accessible password fields", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.endsWith("/api/v1/citizen-auth/me")) return json({ message: "Citizen authentication required." }, 401);
    if (url.endsWith("/api/v1/citizen-auth/sign-up") && init?.method === "POST") return json({ message: "Check your email" }, 202);
    return Promise.reject(new Error(`Unexpected request ${url}`));
  });
  window.history.replaceState({}, "", "/sign-up"); render(<App />); const user = userEvent.setup();
  await user.type(await screen.findByLabelText("Name"), "Civic Citizen"); await user.type(screen.getByLabelText("Email"), "citizen@example.com");
  await user.type(screen.getByLabelText("Password"), "correct horse battery staple"); await user.type(screen.getByLabelText("Confirm password"), "correct horse battery staple");
  await user.click(screen.getByRole("button", { name: "Create account" }));
  expect(await screen.findByRole("heading", { name: "Check your email" })).toBeInTheDocument();
});

test("citizen sign in presents Google and generic credential error", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/api/v1/citizen-auth/me") ? json({}, 401) : json({ message: "Email or password is incorrect." }, 401));
  window.history.replaceState({}, "", "/sign-in"); render(<App />); const user = userEvent.setup();
  expect(await screen.findByRole("link", { name: "Continue with Google" })).toHaveAttribute("href", "/api/v1/citizen-auth/google/start");
  await user.type(screen.getByLabelText("Email"), "unknown@example.com"); await user.type(screen.getByLabelText("Password"), "wrong but sufficiently long"); await user.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Email or password is incorrect.");
});

test("My Complaints renders only the account-scoped response", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input); if (url.endsWith("/api/v1/citizen-auth/me")) return json(session);
    if (url.endsWith("/api/v1/citizen/complaints")) return json({ items: [{ complaint_id: "complaint-1", image_ref: null, description: "Broken street light", latitude: null, longitude: null, location_label: null, location_precision: null, location_details: null, location_source: null, location_accuracy_m: null, status: "submitted", created_at: "2026-10-03T00:00:00Z", updated_at: "2026-10-03T00:00:00Z", history: [] }], page: 1, page_size: 20, total: 1, total_pages: 1 });
    return Promise.reject(new Error(`Unexpected request ${url}`));
  });
  window.history.replaceState({}, "", "/my-complaints"); render(<App />);
  expect(await screen.findByRole("heading", { name: "My Complaints" })).toBeInTheDocument();
  expect(await screen.findByText("Broken street light")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Profile.*Civic Citizen/ })).toBeInTheDocument();
});

test("municipal staff routes use role-neutral visible paths", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/api/v1/auth/me") ? json({}, 401) : Promise.reject(new Error("Unexpected request")));
  window.history.replaceState({}, "", "/staff/sign-in"); render(<App />);
  expect(await screen.findByRole("heading", { name: "Municipal staff sign in" })).toBeInTheDocument();
  expect(screen.queryByText(/sign up as operator/i)).not.toBeInTheDocument();
});

test("invited staff choose credentials but cannot choose role or departments", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    if (String(input).endsWith("/api/v1/staff/accept-invite") && init?.method === "POST") return json({ message: "activated", username: "invited.operator" }, 201);
    return Promise.reject(new Error("Unexpected request"));
  });
  window.history.replaceState({}, "", "/staff/accept-invite?token=test-invitation-token-value-long-enough"); render(<App />); const user = userEvent.setup();
  await user.type(await screen.findByLabelText("Display name"), "Invited Operator"); await user.type(screen.getByLabelText("Username"), "invited.operator");
  await user.type(screen.getByLabelText("Password"), "staff-password-is-long"); await user.type(screen.getByLabelText("Confirm password"), "staff-password-is-long");
  expect(screen.queryByLabelText("Role")).not.toBeInTheDocument(); expect(screen.queryByLabelText(/department/i)).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Activate municipal account" }));
  expect(await screen.findByText("Account activated")).toBeInTheDocument();
});
