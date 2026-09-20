import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

const complaint = {
  complaint_id: "58c6a21d-e82c-4ee2-88aa-e56d86a14ce5",
  description: "Large pothole near the school entrance",
  latitude: 22.5726,
  longitude: 88.3639,
  status: "submitted",
  created_at: "2026-09-20T08:00:00Z",
  updated_at: "2026-09-20T08:00:00Z",
};

function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

test("loads and renders stored complaints", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([complaint]));
  render(<App />);

  expect(screen.getByText("Loading complaints")).toBeInTheDocument();
  expect(await screen.findByText(complaint.description)).toBeInTheDocument();
  expect(screen.getByText("22.5726, 88.3639")).toBeInTheDocument();
});

test("shows an empty state", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  render(<App />);

  expect(await screen.findByText("No complaints yet")).toBeInTheDocument();
});

test("validates the form before sending", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");

  await user.type(screen.getByLabelText("Latitude"), "91");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));

  expect(screen.getByText("Tell us what needs attention.")).toBeInTheDocument();
  expect(screen.getByText("Latitude must be between -90 and 90.")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("submits a valid complaint and adds it to the queue", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse(complaint, 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");

  await user.type(screen.getByLabelText(/What is happening/), complaint.description);
  await user.type(screen.getByLabelText("Latitude"), "22.5726");
  await user.type(screen.getByLabelText("Longitude"), "88.3639");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));

  expect(await screen.findByRole("status")).toHaveTextContent("Complaint #58c6a21d was submitted.");
  expect(screen.getByText(complaint.description)).toBeInTheDocument();
  expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/complaints", expect.objectContaining({ method: "POST" }));
});

test("keeps form contents when submission fails", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockRejectedValueOnce(new TypeError("network failure"));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");

  const description = screen.getByLabelText(/What is happening/);
  await user.type(description, complaint.description);
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("could not be reached");
  expect(description).toHaveValue(complaint.description);
});

test("offers a retry when the complaint list is unavailable", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockRejectedValueOnce(new TypeError("network failure"))
    .mockImplementationOnce(() => jsonResponse([complaint]));
  const user = userEvent.setup();
  render(<App />);

  expect(await screen.findByText("Queue unavailable")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Try again" }));

  await waitFor(() => expect(screen.getByText(complaint.description)).toBeInTheDocument());
  expect(fetchMock).toHaveBeenCalledTimes(2);
});
