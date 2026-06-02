import { useEffect, useState } from "react";
import LoginView from "../features/auth/ui/LoginView";
import { useAuthSession } from "../features/auth/model/useAuthSession";
import AuditLogsPage from "../features/audit/ui/AuditLogsPage";
import EmailPage from "../features/email/ui/EmailPage";
import TasksPage from "../features/tasks/ui/TasksPage";

const THEME_STORAGE_KEY = "fluxboard.ui.theme";
const THEME_OPTIONS = ["fluxboard", "light", "corporate"];

function getInitialTheme() {
  if (typeof window === "undefined") {
    return "fluxboard";
  }

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  return THEME_OPTIONS.includes(storedTheme) ? storedTheme : "fluxboard";
}

export default function App() {
  const { authUser, accessToken, login, register, withAuthenticatedRequest, logout } = useAuthSession();
  const [page, setPage] = useState("tasks");
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  let content;

  if (!authUser) {
    content = <LoginView onLogin={login} onRegister={register} />;
  } else if (page === "audit") {
    content = (
      <AuditLogsPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
        onShowTasks={() => setPage("tasks")}
        onShowEmail={() => setPage("email")}
        onLogout={logout}
      />
    );
  } else if (page === "email") {
    content = (
      <EmailPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
        onShowTasks={() => setPage("tasks")}
        onShowAudit={() => setPage("audit")}
        onLogout={logout}
      />
    );
  } else {
    content = (
      <TasksPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
        onShowAudit={() => setPage("audit")}
        onShowEmail={() => setPage("email")}
        onLogout={logout}
      />
    );
  }

  return (
    <div data-theme={theme} className="min-h-screen bg-base-100 text-base-content">
      <div className="fixed right-4 top-4 z-50">
        <label className="form-control w-40 rounded-xl border border-base-300 bg-base-100/95 p-2 shadow-lg backdrop-blur">
          <span className="label pb-1 pt-0">
            <span className="label-text font-mono text-[11px] uppercase tracking-wide text-base-content/70">
              Theme
            </span>
          </span>
          <select
            className="select select-bordered select-sm"
            value={theme}
            onChange={(event) => setTheme(event.target.value)}
          >
            <option value="fluxboard">Fluxboard</option>
            <option value="light">Light</option>
            <option value="corporate">Corporate</option>
          </select>
        </label>
      </div>
      {content}
    </div>
  );
}
