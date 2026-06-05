import { useEffect, useState } from "react";
import LoginView from "../features/auth/ui/LoginView";
import { useAuthSession } from "../features/auth/model/useAuthSession";
import AuditLogsPage from "../features/audit/ui/AuditLogsPage";
import EmailPage from "../features/email/ui/EmailPage";
import RolesPage from "../features/roles/ui/RolesPage";
import TasksPage from "../features/tasks/ui/TasksPage";

const THEME_STORAGE_KEY = "fluxboard.ui.theme";
const THEME_OPTIONS = ["fluxboard", "light", "corporate"];
const PAGE_TO_PATH = {
  tasks: "/task",
  audit: "/audit",
  email: "/email",
  roles: "/role",
};

const PATH_TO_PAGE = {
  "/task": "tasks",
  "/tasks": "tasks",
  "/user": "tasks",
  "/audit": "audit",
  "/email": "email",
  "/role": "roles",
  "/roles": "roles",
};

function getPageFromPath(pathname) {
  return PATH_TO_PAGE[pathname] || "tasks";
}

function getInitialTheme() {
  if (typeof window === "undefined") {
    return "fluxboard";
  }

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  return THEME_OPTIONS.includes(storedTheme) ? storedTheme : "fluxboard";
}

export default function App() {
  const { authUser, accessToken, login, register, withAuthenticatedRequest, logout } = useAuthSession();
  const [page, setPage] = useState(() => {
    if (typeof window === "undefined") {
      return "tasks";
    }
    return getPageFromPath(window.location.pathname);
  });
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const handlePopState = () => {
      setPage(getPageFromPath(window.location.pathname));
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || !authUser) {
      return;
    }

    const expectedPath = PAGE_TO_PATH[page] || PAGE_TO_PATH.tasks;
    if (window.location.pathname !== expectedPath) {
      window.history.replaceState({}, "", expectedPath);
    }
  }, [authUser, page]);

  function navigateToPage(nextPage) {
    setPage(nextPage);

    if (typeof window === "undefined" || !authUser) {
      return;
    }

    const nextPath = PAGE_TO_PATH[nextPage] || PAGE_TO_PATH.tasks;
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }
  }

  let content;

  if (!authUser) {
    content = <LoginView onLogin={login} onRegister={register} />;
  } else if (page === "audit") {
    content = (
      <AuditLogsPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
      />
    );
  } else if (page === "email") {
    content = (
      <EmailPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
      />
    );
  } else if (page === "roles") {
    content = (
      <RolesPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
      />
    );
  } else {
    content = (
      <TasksPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
      />
    );
  }

  const menuItems = [
    { id: "tasks", label: "Tasks" },
    { id: "audit", label: "Audit Logs" },
    { id: "email", label: "Email" },
    { id: "roles", label: "Roles" },
  ];

  const shell = (
    <div className="mx-auto w-full max-w-[1440px] px-3 py-4 sm:px-6 lg:px-8">
      <div className="grid gap-4 lg:grid-cols-[280px_minmax(760px,1fr)] lg:gap-6">
        <aside className="card border border-base-200 bg-base-100 shadow-xl lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)]">
          <div className="card-body p-5">
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-primary">Task Management API</p>
            <h1 className="text-2xl font-bold tracking-tight">Fluxboard</h1>
            <small className="font-mono text-xs text-base-content/60">v0.6</small>

            <div className="mt-2 rounded-xl border border-base-300 bg-base-200 px-3 py-2">
              <p className="font-mono text-[11px] uppercase tracking-wide text-base-content/70">Signed in as</p>
              <p className="truncate text-sm font-semibold text-base-content">{authUser}</p>
            </div>

            <nav className="mt-3 grid gap-2">
              {menuItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => navigateToPage(item.id)}
                  className={`btn justify-start ${page === item.id ? "btn-primary" : "btn-ghost border border-base-300"}`}
                >
                  {item.label}
                </button>
              ))}
            </nav>

            <div className="mt-auto space-y-3">
              <label className="form-control rounded-xl border border-base-300 bg-base-100 p-2">
                <span className="label pb-1 pt-0">
                  <span className="label-text font-mono text-[11px] uppercase tracking-wide text-base-content/70">Theme</span>
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

              <button type="button" onClick={logout} className="btn btn-primary w-full">
                Logout
              </button>
            </div>
          </div>
        </aside>

        <main className="mx-auto w-full max-w-5xl">{content}</main>
      </div>
    </div>
  );

  return (
    <div data-theme={theme} className="min-h-screen bg-base-100 text-base-content">
      {authUser ? shell : content}
    </div>
  );
}
