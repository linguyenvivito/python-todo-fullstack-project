import type {
  ApiRequestOptions,
  EmailPayloadManual,
  EmailPayloadTemplate,
  EmailTemplate,
} from "../../../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8888";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T = unknown>(path: string, accessToken: string, options: ApiRequestOptions = {}): Promise<T | null> {
  const headers: Record<string, string> = {};
  if (options.body) {
    headers["Content-Type"] = "application/json";
  }
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    ...options,
  });

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        errorMessage = payload.detail;
      }
    } catch {
      const text = await response.text();
      if (text) {
        errorMessage = text;
      }
    }
    throw new ApiError(errorMessage, response.status);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function getEmailTemplates(accessToken: string): Promise<{ items: EmailTemplate[] }> {
  return request<{ items: EmailTemplate[] }>("/email/templates", accessToken);
}

export function sendEmail(
  accessToken: string,
  payload: EmailPayloadManual | EmailPayloadTemplate
): Promise<{ detail?: string }> {
  return request<{ detail?: string }>("/email/send", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export { ApiError };
