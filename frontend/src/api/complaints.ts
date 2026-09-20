export type Complaint = {
  complaint_id: string;
  image_ref: string | null;
  description: string;
  latitude: number | null;
  longitude: number | null;
  status: "submitted";
  created_at: string;
  updated_at: string;
};

export type ComplaintInput = {
  image?: File;
  description: string;
  latitude?: number;
  longitude?: number;
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
  if (input.image) body.append("image", input.image);
  return request<Complaint>("/api/v1/complaints", {
    method: "POST",
    body,
  });
}

export function imageUrl(reference: string): string {
  return apiBaseUrl + reference;
}
