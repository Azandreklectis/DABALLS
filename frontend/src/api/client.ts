
const API_BASE_URL = "/api";

// This Vite variable is intended for local/demo configuration only.
// Values bundled into browser JavaScript are public, not production secrets.
const API_TOKEN = import.meta.env.VITE_DABALLS_API_TOKEN?.trim();

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      "Cannot connect to the DABALLS controller. Check that it is running.",
    );
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const body: unknown = await response.json();

      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof body.detail === "string"
      ) {
        message = body.detail;
      }
    } catch {
      // Keep the default message if the response isn't JSON.
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}