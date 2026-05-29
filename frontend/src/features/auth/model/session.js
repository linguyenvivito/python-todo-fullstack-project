export const AUTH_SESSION_KEY = "fluxboard.auth.user";

export function getStoredUser() {
  return sessionStorage.getItem(AUTH_SESSION_KEY) || "";
}

export function storeUser(username) {
  sessionStorage.setItem(AUTH_SESSION_KEY, username);
}

export function clearStoredUser() {
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}
