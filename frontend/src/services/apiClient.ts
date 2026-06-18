/**
 * Core API client configuration.
 * This is the base fetch wrapper for all HTTP requests.
 */

const API_BASE_URL = "http://127.0.0.1:8888";

export interface ApiRequestOptions extends Omit<RequestInit, "headers"> {
  headers?: Record<string, string>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Make a fetch request to the API.
 * Automatically adds base URL and returns parsed JSON.
 */
export async function apiRequest<T>(
  endpoint: string,
  options?: ApiRequestOptions
): Promise<T> {
  const url = new URL(endpoint, API_BASE_URL);
  const response = await fetch(url.toString(), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorMessage = await response
      .text()
      .then((text) => {
        try {
          const json = JSON.parse(text);
          return json.detail || json.message || response.statusText;
        } catch {
          return text || response.statusText;
        }
      })
      .catch(() => response.statusText);

    throw new ApiError(response.status, errorMessage);
  }

  return response.json();
}

/**
 * Make an authenticated fetch request with Bearer token.
 */
export async function apiRequestAuth<T>(
  endpoint: string,
  token: string,
  options?: ApiRequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}
