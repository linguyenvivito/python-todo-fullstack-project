import { useState } from "react";
import { clearStoredUser, getStoredUser, storeUser } from "./session";

export function useAuthSession() {
  const [authUser, setAuthUser] = useState(() => getStoredUser());

  function login(rawUsername, rawPassword) {
    const username = rawUsername.trim();
    const password = rawPassword.trim();

    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    storeUser(username);
    setAuthUser(username);
  }

  function logout() {
    clearStoredUser();
    setAuthUser("");
  }

  return {
    authUser,
    login,
    logout,
  };
}
