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
  location_source: "map" as const,
  location_accuracy_m: null,
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

const reverseResult = {
  provider_id: "reverse-1",
  label: "BT Road, Baranagar, West Bengal, India",
  latitude: 22.51,
  longitude: 88.41,
  precision: "approximate",
};

function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

type ApiOptions = {
  autocomplete?: boolean;
  complaints?: typeof complaint[];
  searchResults?: typeof broadResult[];
  searchFailure?: boolean;
  reverseFailure?: boolean;
  submitFailure?: boolean;
  listFailures?: number;
};

function installApi(options: ApiOptions = {}) {
  let remainingListFailures = options.listFailures ?? 0;
  return vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.endsWith("/api/v1/location-capabilities")) {
      return jsonResponse({ autocomplete: options.autocomplete ?? false, reverse_geocoding: true });
    }
    if (url.endsWith("/api/v1/location-search")) {
      if (options.searchFailure) return Promise.reject(new TypeError("network failure"));
      return jsonResponse(options.searchResults ?? [broadResult]);
    }
    if (url.endsWith("/api/v1/location-reverse")) {
      if (options.reverseFailure) return Promise.reject(new TypeError("network failure"));
      return jsonResponse(reverseResult);
    }
    if (url.endsWith("/api/v1/complaints") && init?.method === "POST") {
      if (options.submitFailure) return Promise.reject(new TypeError("network failure"));
      return jsonResponse(complaint, 201);
    }
    if (url.endsWith("/api/v1/complaints")) {
      if (remainingListFailures > 0) {
        remainingListFailures -= 1;
        return Promise.reject(new TypeError("network failure"));
      }
      return jsonResponse(options.complaints ?? []);
    }
    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
}

function mockLocation(result: "success" | "denied" | "timeout" | "unavailable" = "success") {
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: {
    getCurrentPosition: vi.fn((success: PositionCallback, failure: PositionErrorCallback) => {
      if (result === "success") {
        success({ coords: { latitude: 22.5, longitude: 88.3, accuracy: 12 } } as GeolocationPosition);
      } else {
        failure({ code: result === "denied" ? 1 : result === "timeout" ? 3 : 2 } as GeolocationPositionError);
      }
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
  await user.click(await screen.findByRole("button", { name: "Confirm this location" }));
}

beforeEach(() => mockLocation());

test("loads stored complaints with truthful location context", async () => {
  installApi({ complaints: [complaint] });
  render(<App />);
  expect(screen.getByText("Loading complaints")).toBeInTheDocument();
  expect(await screen.findByText(complaint.description)).toBeInTheDocument();
  expect(screen.getByText(complaint.location_label)).toBeInTheDocument();
  expect(screen.getByText("Confirmed point")).toBeInTheDocument();
});

test("shows an empty state", async () => {
  installApi();
  render(<App />);
  expect(await screen.findByText("No complaints yet")).toBeInTheDocument();
});

test("requires description photo and confirmed location before sending", async () => {
  const fetchMock = installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  expect(screen.getByText("Tell us what needs attention.")).toBeInTheDocument();
  expect(screen.getByText("Attach a JPEG or PNG photo of the issue.")).toBeInTheDocument();
  expect(screen.getByText("Search for or capture the issue location, then confirm it.")).toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/api/v1/complaints"))).toHaveLength(1);
});

test("submits photo, device source and browser accuracy", async () => {
  const fetchMock = installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByLabelText(/What is happening/), complaint.description);
  const file = await attachPhoto(user);
  await confirmCurrentLocation(user);
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  await screen.findByText(/was submitted/);
  const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST" && init.body instanceof FormData);
  const body = post?.[1]?.body as FormData;
  expect(body.get("image")).toBe(file);
  expect(body.get("location_source")).toBe("device");
  expect(body.get("location_accuracy_m")).toBe("12");
});

test("explicit search selects a result, opens the map and submits search source", async () => {
  const fetchMock = installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByRole("combobox"), "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  await user.click(await screen.findByRole("option", { name: /Baranagar/ }));
  expect(await screen.findByRole("button", { name: "Mock move pin" })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Confirm this location" }));
  await user.type(screen.getByLabelText(/What is happening/), "Blocked drain");
  await attachPhoto(user);
  await user.click(screen.getByRole("button", { name: "Submit complaint" }));
  const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST" && init.body instanceof FormData);
  expect((post?.[1]?.body as FormData).get("location_source")).toBe("search");
});

test("autocomplete shows suggestions after a short debounce", async () => {
  const fetchMock = installApi({ autocomplete: true });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await screen.findByText("Suggestions update while you type.");
  await user.type(screen.getByRole("combobox"), "Baranagar");
  expect(await screen.findByRole("option", { name: /Baranagar/ }, { timeout: 1500 })).toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/api/v1/location-search"))).toHaveLength(1);
});

test("an in-flight search cannot show suggestions for an edited query", async () => {
  let finishSearch!: (response: Response) => void;
  const pendingSearch = new Promise<Response>((resolve) => { finishSearch = resolve; });
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/location-capabilities")) {
      return jsonResponse({ autocomplete: false, reverse_geocoding: true });
    }
    if (url.endsWith("/api/v1/location-search")) return pendingSearch;
    if (url.endsWith("/api/v1/complaints")) return jsonResponse([]);
    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  const input = screen.getByRole("combobox");
  await user.type(input, "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  await user.clear(input);
  await user.type(input, "Kolkata");
  await act(async () => finishSearch(await jsonResponse([broadResult])));
  expect(input).toHaveValue("Kolkata");
  expect(screen.queryByRole("option", { name: /Baranagar/ })).not.toBeInTheDocument();
});

test("keyboard Enter selects the active suggestion", async () => {
  installApi({ autocomplete: true });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByRole("combobox"), "Baranagar");
  await screen.findByRole("option", { name: /Baranagar/ }, { timeout: 1500 });
  await user.keyboard("{Enter}");
  expect(screen.getByText("Review issue location")).toBeInTheDocument();
});

test("short search is rejected locally", async () => {
  const fetchMock = installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByRole("combobox"), "BT");
  await user.click(screen.getByRole("button", { name: "Search" }));
  expect(screen.getByText(/Enter at least 3 characters/)).toBeInTheDocument();
  expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/api/v1/location-search"))).toBe(false);
});

test("no results preserves the complaint draft", async () => {
  installApi({ searchResults: [] });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByLabelText(/What is happening/), "Draft complaint");
  await user.type(screen.getByRole("combobox"), "Unknown place");
  await user.click(screen.getByRole("button", { name: "Search" }));
  expect(await screen.findByText(/No matching locations found/)).toBeInTheDocument();
  expect(screen.getByLabelText(/What is happening/)).toHaveValue("Draft complaint");
});

test("provider failure preserves the complaint draft", async () => {
  installApi({ searchFailure: true });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByLabelText(/What is happening/), "Draft complaint");
  await user.type(screen.getByRole("combobox"), "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  expect(await screen.findByText(/could not be reached/)).toBeInTheDocument();
  expect(screen.getByLabelText(/What is happening/)).toHaveValue("Draft complaint");
});

test("current location requests higher accuracy, reverse lookup and confirmation", async () => {
  installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(navigator.geolocation.getCurrentPosition).toHaveBeenCalledWith(
    expect.any(Function), expect.any(Function),
    { enableHighAccuracy: true, timeout: 30_000, maximumAge: 300_000 },
  );
  expect(await screen.findByText(reverseResult.label)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Confirm this location" }));
  expect(screen.getByText("Confirmed issue location")).toBeInTheDocument();
});

test.each(["denied", "timeout", "unavailable"] as const)("location %s points the user to search", async (result) => {
  mockLocation(result);
  installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText(/(blocked|within 30 seconds|could not be determined).*Search/i)).toBeInTheDocument();
});

test("browser without geolocation directs the user to search", async () => {
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: undefined });
  installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  expect(screen.getByText(/does not support location.*Search/i)).toBeInTheDocument();
});

test("a late device callback cannot replace a searched location", async () => {
  let onSuccess: PositionCallback = () => undefined;
  Object.defineProperty(navigator, "geolocation", { configurable: true, value: {
    getCurrentPosition: vi.fn((success: PositionCallback) => { onSuccess = success; }),
  } });
  installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.click(screen.getByRole("button", { name: "Use my current location" }));
  await user.type(screen.getByRole("combobox"), "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  await user.click(await screen.findByRole("option", { name: /Baranagar/ }));
  act(() => onSuccess({ coords: { latitude: 21, longitude: 87, accuracy: 10 } } as GeolocationPosition));
  expect(screen.getByText(broadResult.label)).toBeInTheDocument();
});

test("map adjustment reverse-geocodes and invalidates confirmation", async () => {
  installApi();
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await confirmCurrentLocation(user);
  await user.click(screen.getByRole("button", { name: "Mock move pin" }));
  expect(await screen.findByText(reverseResult.label)).toBeInTheDocument();
  expect(screen.getByText("Review issue location")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Confirm this location" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Move north/i })).not.toBeInTheDocument();
});

test("reverse lookup failure retains the moved point for confirmation", async () => {
  installApi({ reverseFailure: true });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("No complaints yet");
  await user.type(screen.getByRole("combobox"), "Baranagar");
  await user.click(screen.getByRole("button", { name: "Search" }));
  await user.click(await screen.findByRole("option", { name: /Baranagar/ }));
  await user.click(screen.getByRole("button", { name: "Mock move pin" }));
  expect(await screen.findByText(/address could not be refreshed/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Confirm this location" })).toBeEnabled();
});

test("keeps all form contents when submission fails", async () => {
  installApi({ submitFailure: true });
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
  installApi({ complaints: [complaint], listFailures: 1 });
  const user = userEvent.setup();
  render(<App />);
  expect(await screen.findByText("Queue unavailable")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByText(complaint.description)).toBeInTheDocument();
});

test("image selection removal and replacement use the final file", async () => {
  installApi();
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
  installApi();
  const user = userEvent.setup({ applyAccept: false });
  render(<App />);
  const file = new File([new Uint8Array(Number(size))], String(name), { type: String(type) });
  await user.upload(screen.getByLabelText("Attach a photo"), file);
  expect(screen.getByRole("alert")).toHaveTextContent(String(message));
});
