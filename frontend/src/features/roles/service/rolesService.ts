import { createRole, deleteRole, getRoles, updateRole } from "../api/rolesApi";
import type { Role, WithAuthenticatedRequest } from "../../../types";

/**
 * Fetch all roles.
 */
export async function fetchRoles(withAuthenticatedRequest: WithAuthenticatedRequest): Promise<Role[]> {
  return withAuthenticatedRequest((token) => getRoles(token));
}

/**
 * Create a new role with validation.
 */
export async function createNewRole(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  name: string
): Promise<void> {
  const trimmedName = name.trim();
  if (!trimmedName) {
    throw new Error("Role name is required");
  }

  await withAuthenticatedRequest((token) =>
    createRole(token, {
      name: trimmedName,
    })
  );
}

/**
 * Update a role by ID with validation.
 */
export async function updateRoleById(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  roleId: number,
  name: string
): Promise<void> {
  const trimmedName = name.trim();
  if (!trimmedName) {
    throw new Error("Role name is required");
  }

  await withAuthenticatedRequest((token) =>
    updateRole(token, roleId, {
      name: trimmedName,
    })
  );
}

/**
 * Delete a role by ID.
 */
export async function deleteRoleById(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  roleId: number
): Promise<void> {
  await withAuthenticatedRequest((token) => deleteRole(token, roleId));
}
