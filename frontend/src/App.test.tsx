import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

vi.mock("./LocationMap", () => ({
  default: ({ onChange }: { onChange: (coordinates: {latitude: number; longitude: number}) => void }) => (
    <button type="button" onClick={() => onChange({ latitude: 22.51, longitude: 88.41 })}>Mock move pin</button>
  ),
}));

const complaint = {
  complaint_id: "58c6a21d-e82c-4ee2-88aa-e56d86a14ce5",
  image_ref: "/api/v1/complaint-images/demo.png",
  description: "Large pothole near the school entrance",
  latitude: 22.5726,
  longitude: 88.3639,
  location_label: "School entrance, Kolkata, West Bengal",
  location_precision: "exact" as const,
  location_details: "Beside the main gate",
  status: "submitted" as const,
  created_at: "2026-09-20T08:00:00Z",
  updated_at: "2026-09-20T08:00:00Z",
};

const broadResult = {
  provider_id: "101",
  label: "Baranagar, North 24 Parganas, West Bengal, India",
  latitude: 22.641,
  longitude: 88.377,
  precision: "broad",
};

function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

function mockLocation(result: "success" | "denied" | "timeout" | "unavailable" = "success") {
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: {
    getCurrentPosition: vi.fn((success, failure) => {
      if (result === "success") success({ coords: { latitude: 22.5, longitude: 88.3 } });
      else failure({ code: result === "denied" ? 1 : result === "timeout" ? 3 : 2 });
    }),
  } });
}

async function attachPhoto(user: ReturnType<typeof userEvent.setup>, name = "issue.png") {
  const file = new File(["png"], name, { type: "image/png" });
  await user.upload(screen.getByLabelText("Attach a photo"), file);
  return file;
}

async function confirmCurrentLocation(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  await user.click(screen.getByRole("button", { name: "Confirm this location" }));
}

beforeEach(() => mockLocation());

test("loads stored complaints with truthful location context", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([complaint]));
  render(<App />);

  expect(screen.getByText("Loading complaints")).toBeInTheDocument();
  expect(await screen.findByText(complaint.description)).toBeInTheDocument();
  expect(screen.getByText(complaint.location_label)).toBeInTheDocument();
  expect(screen.getByText("Confirmed point")).toBeInTheDocument();
  expect(screen.getByText(complaint.location_details)).toBeInTheDocument();
});

test("shows an empty state", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  render(<App />);
  expect(await screen.findByText("No complaints yet")).toBeInTheDocument();
});

test("requires description photo and confirmed location before sending", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");

  await user.click(screen.getByRole("button", { name: "Submit complaint" }));

  expect(screen.getByText("Tell us what needs attention.")).toBeInTheDocument();
  expect(screen.getByText("Attach a JPEG or PNG photo of the issue.")).toBeInTheDocument();
  expect(screen.getByText("Search for or capture the issue location, then confirm it.")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("submits required photo and confirmed current location", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse(complaint, 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");

  const file = await attachPhoto(user);
  await confirmCurrentLocation(user);
  await user.type(screen.getByLabelText(/What is happening/), complaint.description);
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));

  expect(await screen.findByRole("status")).toHaveTextContent("Complaint #58c6a21d was submitted.");
  const body = fetchMock.mock.calls[1][1]?.body as FormData;
  expect(body.get("image")).toBe(file);
  expect(body.get("latitude")).toBe("22.5");
  expect(body.get("longitude")).toBe("88.3");
  expect(body.get("location_label")).toBe("Current device location");
  expect(body.get("location_precision")).toBe("exact");
});

test("searches explicitly, selects without a map and submits broad location honestly", async () => {
  const created = { ...complaint, location_label: broadResult.label, location_precision: "broad" as const, location_details: "Near the bus stop" };
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse([broadResult]))
    .mockImplementationOnce(() => jsonResponse(created, 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");

  await user.type(screen.getByLabelText("Search locality, PIN code, street or landmark"), "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  const result = await screen.findByRole("button", { name: /Baranagar, North 24 Parganas/ });
  await user.click(result);
  expect(screen.queryByLabelText("Map showing the selected issue location")).not.toBeInTheDocument();
  await user.type(screen.getByLabelText(/Nearby details/), "Near the bus stop");
  await user.click(screen.getByRole("button", { name: "Confirm this location" }));
  await attachPhoto(user);
  await user.type(screen.getByLabelText(/What is happening/), "Blocked drain");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  await screen.findByRole("status");

  expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/location-search");
  expect(fetchMock.mock.calls[1][1]?.body).toBe(JSON.stringify({ query: "Baranagar" }));
  const body = fetchMock.mock.calls[2][1]?.body as FormData;
  expect(body.get("location_label")).toBe(broadResult.label);
  expect(body.get("location_precision")).toBe("broad");
  expect(body.get("location_details")).toBe("Near the bus stop");
});

test("short search is rejected locally without an API call", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByLabelText("Search locality, PIN code, street or landmark"), "ab");
  await user.click(screen.getByRole("button", { name: "Search" }));
  expect(screen.getByText(/Enter at least 3 characters/)).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("no search results keeps the draft and offers guidance", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByLabelText(/What is happening/), "Draft complaint");
  await user.type(screen.getByLabelText("Search locality, PIN code, street or landmark"), "Unknown place");
  await user.click(screen.getByRole("button", { name: "Search" }));
  expect(await screen.findByText(/No matching locations found/)).toBeInTheDocument();
  expect(screen.getByLabelText(/What is happening/)).toHaveValue("Draft complaint");
});

test("provider failure keeps the draft", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse({ message: "Location search is temporarily unavailable. Your complaint draft is safe; please try again." }, 503));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByLabelText(/What is happening/), "Draft complaint");
  await user.type(screen.getByLabelText("Search locality, PIN code, street or landmark"), "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  expect(await screen.findByText(/temporarily unavailable/)).toBeInTheDocument();
  expect(screen.getByLabelText(/What is happening/)).toHaveValue("Draft complaint");
});

test("current location uses bounded recent-position options and requires confirmation", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText("Review issue location")).toBeInTheDocument();
  expect(navigator.geolocation.getCurrentPosition).toHaveBeenCalledWith(
    expect.any(Function), expect.any(Function),
    { enableHighAccuracy: false, timeout: 30_000, maximumAge: 300_000 },
  );
  await user.click(screen.getByRole("button", { name: "Confirm this location" }));
  expect(screen.getByText("Confirmed issue location")).toBeInTheDocument();
});

test.each(["denied", "timeout", "unavailable"] as const)("location %s points the user to search", async (result) => {
  mockLocation(result);
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText(/(blocked|within 30 seconds|could not be determined).*Search/i)).toBeInTheDocument();
});

test("browser without geolocation directs the user to search", async () => {
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: undefined });
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText(/does not support location.*Search/i)).toBeInTheDocument();
});

test("a late device callback cannot replace a searched location", async () => {
  let onSuccess: (position: {coords: {latitude: number; longitude: number}}) => void = () => {};
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: {
    getCurrentPosition: vi.fn((success) => { onSuccess = success; }),
  } });
  vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockImplementationOnce(() => jsonResponse([broadResult]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  await user.type(screen.getByLabelText("Search locality, PIN code, street or landmark"), "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  await user.click(await screen.findByRole("button", { name: /Baranagar, North 24 Parganas/ }));
  act(() => onSuccess({coords: {latitude: 21, longitude: 87}}));
  expect(screen.getByText(broadResult.label)).toBeInTheDocument();
  expect(screen.queryByText("Current device location")).not.toBeInTheDocument();
});

test("map adjustment changes precision and invalidates confirmation", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await confirmCurrentLocation(user);
  await user.click(screen.getByRole("button", { name: "Adjust precisely on map" }));
  await user.click(await screen.findByRole("button", { name: "Mock move pin" }));
  expect(screen.getByText("Review issue location")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Confirm this location" })).toBeInTheDocument();
});

test("keeps all form contents when submission fails", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => jsonResponse([]))
    .mockRejectedValueOnce(new TypeError("network failure"));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  const description = screen.getByLabelText(/What is happening/);
  await user.type(description, complaint.description);
  await attachPhoto(user);
  await confirmCurrentLocation(user);
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("could not be reached");
  expect(description).toHaveValue(complaint.description);
  expect(screen.getByText("Selected: issue.png")).toBeInTheDocument();
  expect(screen.getByText("Confirmed issue location")).toBeInTheDocument();
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

test("image selection removal and replacement use the final file", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => jsonResponse([]));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  const input = screen.getByLabelText("Attach a photo");
  await user.upload(input, new File(["png"], "first.png", { type: "image/png" }));
  await user.click(screen.getByRole("button", { name: "Remove image" }));
  expect(screen.queryByText("Selected: first.png")).not.toBeInTheDocument();
  await user.upload(input, new File(["jpeg"], "second.jpg", { type: "image/jpeg" }));
  expect(screen.getByText("Selected: second.jpg")).toBeInTheDocument();
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
});
