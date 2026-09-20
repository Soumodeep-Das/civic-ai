export type Complaint = {
  complaint_id: string;
  image_ref: string | null;
  description: string;
  latitude: number | null;
  longitude: number | null;
  location_label: string | null;
  location_precision: LocationPrecision | null;
  location_details: string | null;
  location_source: LocationSource | null;
  location_accuracy_m: number | null;
  status: "submitted";
  created_at: string;
  updated_at: string;
};

export type LocationPrecision = "exact" | "approximate" | "broad";
export type LocationSource = "search" | "device" | "map";

export type LocationSearchResult = {
  provider_id: string;
  label: string;
  latitude: number;
  longitude: number;
  precision: Exclude<LocationPrecision, "exact">;
};

export type ComplaintInput = {
  image?: File;
  description: string;
  latitude?: number;
  longitude?: number;
  location_label?: string;
  location_precision?: LocationPrecision;
  location_details?: string;
  location_source?: LocationSource;
  location_accuracy_m?: number;
};

type ApiErrorBody = {
  message?: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? "";
const apiBaseUrl = configuredBaseUrl.replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        ...options?.headers,
      },
    });
  } catch {
    throw new ApiError("The complaint service could not be reached. Please try again.", 0);
  }

  if (!response.ok) {
    let body: ApiErrorBody | undefined;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      body = undefined;
    }

    throw new ApiError(body?.message ?? "The complaint service returned an unexpected error.", response.status);
  }

  return response.json() as Promise<T>;
}

export function listComplaints(): Promise<Complaint[]> {
  return request<Complaint[]>("/api/v1/complaints");
}

export function createComplaint(input: ComplaintInput): Promise<Complaint> {
  const body = new FormData();
  body.append("description", input.description);
  if (input.latitude !== undefined) body.append("latitude", String(input.latitude));
  if (input.longitude !== undefined) body.append("longitude", String(input.longitude));
  if (input.location_label !== undefined) body.append("location_label", input.location_label);
  if (input.location_precision !== undefined) body.append("location_precision", input.location_precision);
  if (input.location_details !== undefined) body.append("location_details", input.location_details);
  if (input.location_source !== undefined) body.append("location_source", input.location_source);
  if (input.location_accuracy_m !== undefined) body.append("location_accuracy_m", String(input.location_accuracy_m));
  if (input.image) body.append("image", input.image);
  return request<Complaint>("/api/v1/complaints", {
    method: "POST",
    body,
  });
}

export function searchLocations(query: string): Promise<LocationSearchResult[]> {
  return request<LocationSearchResult[]>("/api/v1/location-search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
}

export function getLocationCapabilities(): Promise<{ autocomplete: boolean; reverse_geocoding: boolean }> {
  return request("/api/v1/location-capabilities");
}

export function reverseLocation(latitude: number, longitude: number): Promise<LocationSearchResult | null> {
  return request<LocationSearchResult | null>("/api/v1/location-reverse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ latitude, longitude }),
  });
}

export function imageUrl(reference: string): string {
  return apiBaseUrl + reference;
}
