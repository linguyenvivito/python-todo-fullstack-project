import { User } from "../types";

interface ChildComponentProps {
  // Define the props that the child component will receive
  user: User;
  onClose: () => void;
}

export const UserView: React.FC<ChildComponentProps> = ({ user, onClose }) => {
  return (
    <section className="card mt-4 border border-base-200 shadow-xl overflow-hidden">
      <div className="border-b border-base-200 bg-base-200 px-4 py-3">
        <p className="font-mono text-xs uppercase tracking-wide text-base-content/70">
          User Details
        </p>
        <p>{user.username}</p>
      </div>
<button
        className="btn btn-sm btn-outline mt-4"
        onClick={onClose}
        >
        Close
      </button>
      </section>
  );
};
