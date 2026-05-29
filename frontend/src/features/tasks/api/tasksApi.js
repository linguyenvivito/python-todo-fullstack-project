const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8888";

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
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function getTasks(accessToken) {
  return request("/tasks", accessToken);
}

export function getTasksByStatus(accessToken, status) {
  return request(`/tasks/status/${status}`, accessToken);
}

export function createTask(accessToken, payload) {
  return request("/tasks", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTask(accessToken, taskId, payload) {
  return request(`/tasks/${taskId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTask(accessToken, taskId) {
  return request(`/tasks/${taskId}`, accessToken, {
    method: "DELETE",
  });
}
