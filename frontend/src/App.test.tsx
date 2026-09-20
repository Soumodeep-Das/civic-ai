import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

const complaint = {
  complaint_id: "58c6a21d-e82c-4ee2-88aa-e56d86a14ce5",
  image_ref: null,
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
  expect(screen.getByText("Location provided")).toBeInTheDocument();
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

  expect(screen.queryByLabelText("Latitude")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("Longitude")).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));

  expect(screen.getByText("Tell us what needs attention.")).toBeInTheDocument();

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

function mockLocation(result: "success" | "denied" | "timeout" | "unavailable") {
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: {
    getCurrentPosition: vi.fn((success, failure) => {
      if (result === "success") success({ coords: { latitude: 22.5, longitude: 88.3 } });
      else failure({ code: result === "denied" ? 1 : result === "timeout" ? 3 : 2 });
    }),
  } });
}

test("captures location and sends multipart coordinates", async () => {
  mockLocation("success");
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse(complaint, 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText("Location captured successfully")).toBeInTheDocument();
  expect(navigator.geolocation.getCurrentPosition).toHaveBeenCalledWith(
    expect.any(Function),
    expect.any(Function),
    { enableHighAccuracy: false, timeout: 30_000, maximumAge: 300_000 },
  );
  await user.type(screen.getByLabelText(/What is happening/), "Issue");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  await screen.findByRole("status");
  const body = fetchMock.mock.calls[1][1]?.body as FormData;
  expect(body.get("latitude")).toBe("22.5");
  expect(body.get("longitude")).toBe("88.3");
});

test.each(["denied", "timeout", "unavailable"] as const)("location %s allows submission", async (result) => {
  mockLocation(result);
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse(complaint, 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText(/(permission denied|not available within 30 seconds|could not be determined)/)).toBeInTheDocument();
  await user.type(screen.getByLabelText(/What is happening/), "Issue");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  await screen.findByRole("status");
  const body = fetchMock.mock.calls[1][1]?.body as FormData;
  expect(body.has("latitude")).toBe(false);
  expect(body.has("longitude")).toBe(false);
});

test("browser without geolocation shows guidance", async () => {
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: undefined });
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText(/does not support location/)).toBeInTheDocument();
});

test("late location callback cannot restore a location the user removed", async () => {
  let onSuccess: (position: {coords: {latitude: number; longitude: number}}) => void = () => {};
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: {
    getCurrentPosition: vi.fn((success) => { onSuccess = success; }),
  } });
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse(complaint, 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  await user.click(screen.getByRole("button", { name: "Continue without location" }));
  act(() => onSuccess({coords: {latitude: 22, longitude: 88}}));
  expect(screen.queryByText("Location captured successfully")).not.toBeInTheDocument();
  await user.type(screen.getByLabelText(/What is happening/), "Issue");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  await screen.findByRole("status");
  expect((fetchMock.mock.calls[1][1]?.body as FormData).has("latitude")).toBe(false);
});

test("image selection removal replacement and multipart upload", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse({ ...complaint, image_ref: "/api/v1/complaint-images/demo.png" }, 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  const input = screen.getByLabelText("Attach a photo");
  await user.upload(input, new File(["png"], "first.png", { type: "image/png" }));
  expect(screen.getByText("Selected: first.png")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Remove image" }));
  expect(screen.queryByText("Selected: first.png")).not.toBeInTheDocument();
  const file = new File(["jpeg"], "second.jpg", { type: "image/jpeg" });
  await user.upload(input, file);
  await user.type(screen.getByLabelText(/What is happening/), "Issue");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  await screen.findByRole("status");
  const body = fetchMock.mock.calls[1][1]?.body as FormData;
  expect(body.get("image")).toBe(file);
  expect(screen.getByAltText("Photo attached to this complaint")).toHaveAttribute("src", "/api/v1/complaint-images/demo.png");
});

test.each([
  ["video.mp4", "video/mp4", 10, "Choose a JPEG or PNG image."],
  ["huge.png", "image/png", 5 * 1024 * 1024 + 1, "Image must be 5 MiB or smaller."],
])("rejects invalid image %s", async (name, type, size, message) => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup({ applyAccept: false });
  render(<App />);
  const file = new File([new Uint8Array(Number(size))], String(name), { type: String(type) });
  await user.upload(screen.getByLabelText("Attach a photo"), file);
  expect(screen.getByRole("alert")).toHaveTextContent(String(message));
  await user.click(screen.getByRole("button", { name: "Remove image" }));
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
