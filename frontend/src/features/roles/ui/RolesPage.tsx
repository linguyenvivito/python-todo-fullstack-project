import { useRoles } from "../storage/useRoles";

export default function RolesPage({
  authUser,
  accessToken,
  withAuthenticatedRequest,
}) {
  const {
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
  } = useRoles(accessToken, withAuthenticatedRequest);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="card border border-base-200 shadow-xl">
        <div className="card-body p-6 sm:p-8">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-primary">
            Task Management API
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-base-content sm:text-5xl">Role Console</h1>
          <small className="mt-1 block font-mono text-xs text-base-content/60">v0.6</small>
          <p className="mt-3 max-w-3xl text-sm text-base-content/70 sm:text-base">
            Manage authorization roles from the frontend and sync directly with your FastAPI API.
          </p>

          <div className="mt-5">
            <span className="font-mono text-xs uppercase tracking-wide text-base-content/70">
              Signed in as {authUser}
            </span>
          </div>
        </div>
      </header>

      <section className="card mt-4 border border-base-200 shadow-xl">
        <div className="card-body p-4 sm:p-5">
          <form onSubmit={createNewRole} className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="admin"
              maxLength={100}
              className="input input-bordered w-full"
            />

            <div className="flex gap-2">
              <button type="submit" disabled={submitting} className="btn btn-primary btn-sm">
                {submitting ? "Creating..." : "Create Role"}
              </button>
              <button type="button" onClick={loadRoles} disabled={loading} className="btn btn-outline btn-sm">
                Refresh
              </button>
            </div>
          </form>
        </div>
      </section>

      {error && (
        <div className="alert alert-error mt-4">
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="alert alert-warning mt-4">
          <span>Loading roles...</span>
        </div>
      )}

      <section className="card mt-4 border border-base-200 shadow-xl overflow-hidden">
        <div className="border-b border-base-200 bg-base-200 px-4 py-3">
          <p className="font-mono text-xs uppercase tracking-wide text-base-content/70">
            Total roles: {roles.length}
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="table table-zebra w-full min-w-[640px]">
            <thead>
              <tr>
                <th className="font-mono text-[11px] uppercase tracking-wide">ID</th>
                <th className="font-mono text-[11px] uppercase tracking-wide">Name</th>
                <th className="font-mono text-[11px] uppercase tracking-wide text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {roles.map((role) => (
                <tr key={role.id}>
                  <td className="font-mono text-xs text-base-content">{role.id}</td>
                  <td className="text-sm text-base-content">
                    {editingRoleId === role.id ? (
                      <input
                        type="text"
                        value={editingName}
                        onChange={(event) => setEditingName(event.target.value)}
                        maxLength={100}
                        className="input input-bordered input-sm w-full"
                      />
                    ) : (
                      role.name
                    )}
                  </td>
                  <td className="text-right">
                    <div className="flex justify-end gap-2">
                      {editingRoleId === role.id ? (
                        <>
                          <button
                            type="button"
                            onClick={() => saveRole(role.id)}
                            disabled={savingRoleId === role.id}
                            className="btn btn-xs btn-primary"
                          >
                            {savingRoleId === role.id ? "Saving..." : "Save"}
                          </button>
                          <button
                            type="button"
                            onClick={cancelEditRole}
                            className="btn btn-xs btn-outline"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          onClick={() => startEditRole(role)}
                          className="btn btn-xs btn-outline"
                        >
                          Edit
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => removeRole(role.id)}
                        disabled={deletingRoleId === role.id}
                        className="btn btn-xs btn-error btn-outline"
                      >
                        {deletingRoleId === role.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {roles.length === 0 && !loading && (
                <tr>
                  <td colSpan={3} className="py-8 text-center">
                    <span className="text-sm text-base-content/70">No roles found. Create your first role above.</span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
