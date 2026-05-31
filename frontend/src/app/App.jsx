import { useState } from "react";
import LoginView from "../features/auth/ui/LoginView";
import { useAuthSession } from "../features/auth/model/useAuthSession";
import AuditLogsPage from "../features/audit/ui/AuditLogsPage";
import TasksPage from "../features/tasks/ui/TasksPage";

export default function App() {
  const { authUser, accessToken, login, register, withAuthenticatedRequest, logout } = useAuthSession();
  const [page, setPage] = useState("tasks");

  if (!authUser) {
    return <LoginView onLogin={login} onRegister={register} />;
  }

  if (page === "audit") {
    return (
      <AuditLogsPage
        authUser={authUser}
        accessToken={accessToken}
        withAuthenticatedRequest={withAuthenticatedRequest}
        onShowTasks={() => setPage("tasks")}
        onLogout={logout}
      />
    );
  }

  return (
    <TasksPage
      authUser={authUser}
      accessToken={accessToken}
      withAuthenticatedRequest={withAuthenticatedRequest}
      onShowAudit={() => setPage("audit")}
      onLogout={logout}
    />
  );
}
