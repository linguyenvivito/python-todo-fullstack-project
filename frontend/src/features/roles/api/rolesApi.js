const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8888";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, accessToken, options = {}) {
  const headers = {};
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

export function getRoles(accessToken) {
  return request("/roles", accessToken);
}

export function createRole(accessToken, payload) {
  return request("/roles", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRole(accessToken, roleId, payload) {
  return request(`/roles/${roleId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteRole(accessToken, roleId) {
  return request(`/roles/${roleId}`, accessToken, {
    method: "DELETE",
  });
}
