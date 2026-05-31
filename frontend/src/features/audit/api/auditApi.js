const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8888";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, accessToken) {
  const headers = {};
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { headers });
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

  return response.json();
}

export function getAuditLogs(accessToken, query = {}) {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request(`/audit-logs${suffix}`, accessToken);
}

export { ApiError };
