import { useEffect, useState } from "react";
import { User } from "../types";
import { WithAuthenticatedRequest } from "../../../types";
import { fetchUsers } from "../services/usersService";

interface ChildComponentProps {
  // Define the props that the child component will receive
  users: User[];
  onEditUser: (user: User) => void;
  onDeleteUser: (userId: number) => void;
  onViewUserDetails: (userId: number) => void;
  // Add more props as needed
}

export const UserList: React.FC<ChildComponentProps> = ({
  users,
  onEditUser,
  onDeleteUser,
  onViewUserDetails,
}) => {
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [userIdToDelete, setUserIdToDelete] = useState<number | null>(null);

  const handleDeleteUser = (userId: number) => {
    // Show confirmation modal before deleting
    setUserIdToDelete(userId);
    setShowDeleteConfirmation(true);
    // If confirmed, call the onDeleteUser prop
    if (showDeleteConfirmation && userIdToDelete !== null) {
      onDeleteUser(userIdToDelete);
      setShowDeleteConfirmation(false);
      setUserIdToDelete(null);
    }
  };

  return (
    <section className="card mt-4 border border-base-200 shadow-xl overflow-hidden">
      <div className="border-b border-base-200 bg-base-200 px-4 py-3">
        <p className="font-mono text-xs uppercase tracking-wide text-base-content/70">
          Total users: {users.length}
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="table table-zebra w-full min-w-[640px]">
          <thead>
            <tr>
              <th className="font-mono text-[11px] uppercase tracking-wide">
                ID
              </th>
              <th className="font-mono text-[11px] uppercase tracking-wide">
                User Name
              </th>
              <th className="font-mono text-[11px] uppercase tracking-wide text-right">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td className="font-mono text-xs text-base-content">
                  {user.id}
                </td>
                <td className="text-sm text-base-content">{user.username}</td>
                <td className="text-right">
                  <div className="flex justify-end gap-2">
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => onEditUser(user)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-error"
                      onClick={() => handleDeleteUser(user.id)}
                    >
                      Delete
                    </button>
                    <button
                      className="btn btn-sm btn-outline"
                      onClick={() => onViewUserDetails(user.id)}
                    >
                      Details
                    </button>
                  </div>
                </td>
              </tr>
            ))}

            {users.length === 0 && (
              <tr>
                <td colSpan={3} className="py-8 text-center">
                  <span className="text-sm text-base-content/70">
                    No users found. Create your first user above.
                  </span>
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Popup up yes no for confirmation to delete */}
        {showDeleteConfirmation && (
          <div
            className={`modal ${showDeleteConfirmation ? "modal-open" : ""}`}
            role="dialog"
          >
            <div className="modal-box">
              <h3 className="font-bold text-lg">
                Are you sure you want to delete this user?
              </h3>
              <p className="py-4">This action cannot be undone.</p>
              <div className="modal-action">
                <button
                  className="btn btn-error"
                  onClick={() => {
                    if (userIdToDelete !== null) {
                      onDeleteUser(userIdToDelete);
                    }
                    setShowDeleteConfirmation(false);
                    setUserIdToDelete(null);
                  }}
                >
                  Yes
                </button>
                <button
                  className="btn btn-outline"
                  onClick={() => {
                    setShowDeleteConfirmation(false);
                    setUserIdToDelete(null);
                  }}
                >
                  No
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
