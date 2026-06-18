import { useEffect, useState } from "react";
import { WithAuthenticatedRequest } from "../../types";
import { UserList } from "./components/UserList";
import { User } from "./types";
import { fetchUsers } from "./services/usersService";
import { UserView } from "./components/UserView";
import { UserEdit } from "./components/UserEdit";

type UserPageProps = {
  authUser: string;
  accessToken: string;
  withAuthenticatedRequest: WithAuthenticatedRequest;
};

export default function UserPage({ authUser, accessToken, withAuthenticatedRequest }: UserPageProps) {

  const isAuthenticated = Boolean(accessToken);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [deleteUserId, setDeleteUserId] = useState<number | null>(null);
  const [viewUserId, setViewUserId] = useState<number | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
 
  async function loadUsers() {
    try {
      setLoading(true);
      setError("");
      const data = await fetchUsers(withAuthenticatedRequest);
      setUsers(data);
    } catch (err) {
      setError(err.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, [isAuthenticated, withAuthenticatedRequest]);

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="card border border-base-200 shadow-xl">
        <div className="card-body p-6 sm:p-8">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-primary">
            Task Management API
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-base-content sm:text-5xl">User Console</h1>
          <small className="mt-1 block font-mono text-xs text-base-content/60">v0.6</small>
          <p className="mt-3 max-w-3xl text-sm text-base-content/70 sm:text-base">
            View basic account information for the authenticated user.
          </p>

          <div className="mt-5 rounded-2xl border border-base-300 bg-base-200 p-4">
            <p className="font-mono text-[11px] uppercase tracking-wide text-base-content/70">Current user</p>
            <p className="mt-1 text-lg font-semibold text-base-content">{authUser || "Guest"}</p>
          </div>
        </div>
      </header>

      {error && (
        <div className="alert alert-error mt-4">
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="alert alert-warning mt-4">
          <span>Loading tasks...</span>
        </div>
      )}
  
      {currentUser && <UserEdit user={currentUser} onClose={() => setCurrentUser(null)} />}

      {/* if viewUserId or currentUser is not null, hide the user list */}
      {!viewUserId && !currentUser && <UserList users={users} onEditUser={setCurrentUser} onDeleteUser={setDeleteUserId} onViewUserDetails={setViewUserId} />}

      {viewUserId && <UserView user={users.find((user) => user.id === viewUserId) || null} onClose={() => setViewUserId(null)} />}
    </div>
  );
}
