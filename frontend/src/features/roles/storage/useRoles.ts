import { FormEvent, useEffect, useState } from "react";
import { fetchRoles, createNewRole as createRoleService, updateRoleById, deleteRoleById } from "../service/rolesService";
import type { Role, WithAuthenticatedRequest } from "../../../types";

export function useRoles(accessToken: string, withAuthenticatedRequest: WithAuthenticatedRequest) {
  const isAuthenticated = Boolean(accessToken);
  const [roles, setRoles] = useState<Role[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [savingRoleId, setSavingRoleId] = useState(0);
  const [deletingRoleId, setDeletingRoleId] = useState(0);
  const [editingRoleId, setEditingRoleId] = useState(0);
  const [editingName, setEditingName] = useState("");
  const [error, setError] = useState("");

  async function loadRoles() {
    try {
      setLoading(true);
      setError("");
      const data = await fetchRoles(withAuthenticatedRequest);
      setRoles(data);
    } catch (err) {
      setError(err.message || "Failed to load roles");
    } finally {
      setLoading(false);
    }
  }

  async function createNewRole(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError("");
      await createRoleService(withAuthenticatedRequest, name);
      setName("");
      await loadRoles();
    } catch (err) {
      setError(err.message || "Failed to create role");
    } finally {
      setSubmitting(false);
    }
  }

  function startEditRole(role) {
    setError("");
    setEditingRoleId(role.id);
    setEditingName(role.name);
  }

  function cancelEditRole() {
    setEditingRoleId(0);
    setEditingName("");
  }

  async function saveRole(roleId) {
    try {
      setSavingRoleId(roleId);
      setError("");
      await updateRoleById(withAuthenticatedRequest, roleId, editingName);
      setEditingRoleId(0);
      setEditingName("");
      await loadRoles();
    } catch (err) {
      setError(err.message || "Failed to update role");
    } finally {
      setSavingRoleId(0);
    }
  }

  async function removeRole(roleId) {
    try {
      setDeletingRoleId(roleId);
      setError("");
      await deleteRoleById(withAuthenticatedRequest, roleId);
      if (editingRoleId === roleId) {
        setEditingRoleId(0);
        setEditingName("");
      }
      await loadRoles();
    } catch (err) {
      setError(err.message || "Failed to delete role");
    } finally {
      setDeletingRoleId(0);
    }
  }

  useEffect(() => {
    if (!isAuthenticated) {
      setRoles([]);
      setName("");
      setSavingRoleId(0);
      setDeletingRoleId(0);
      setEditingRoleId(0);
      setEditingName("");
      setError("");
      return;
    }

    loadRoles();
  }, [isAuthenticated, accessToken]);

  return {
    roles,
    name,
    setName,
    loading,
    submitting,
    savingRoleId,
    deletingRoleId,
    editingRoleId,
    editingName,
    setEditingName,
    error,
    loadRoles,
    createNewRole,
    startEditRole,
    cancelEditRole,
    saveRole,
    removeRole,
  };
}
