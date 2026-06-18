import { useEffect, useState } from "react";
import { fetchUsers } from "../services/usersService";
import type { WithAuthenticatedRequest } from "../../../types";

import type { User } from "../types";

export function useUsers(accessToken: string, withAuthenticatedRequest: WithAuthenticatedRequest) {
  const isAuthenticated = Boolean(accessToken);
  const [users, setUsers] = useState<User[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      setUsers([]);
      setLoading(false);
      setError("");
      return;
    }

    async function loadUsers() {
      setLoading(true);
      setError("");
      try {
        const response = await fetchUsers(withAuthenticatedRequest);
        setUsers(response || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load users");
      } finally {
        setLoading(false);
      }
    }

    loadUsers();
  }, [isAuthenticated, withAuthenticatedRequest]);

  return {
    isAuthenticated,
    users,
    name,
    setName,
    loading,
    submitting,
    error,
    setUsers,
    setLoading,
    setError,
  };
}
