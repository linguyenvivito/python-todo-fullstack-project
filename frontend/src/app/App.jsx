import LoginView from "../features/auth/ui/LoginView";
import { useAuthSession } from "../features/auth/model/useAuthSession";
import TasksPage from "../features/tasks/ui/TasksPage";

export default function App() {
  const { authUser, accessToken, login, register, withAuthenticatedRequest, logout } = useAuthSession();

  if (!authUser) {
    return <LoginView onLogin={login} onRegister={register} />;
  }

  return (
    <TasksPage
      authUser={authUser}
      accessToken={accessToken}
      withAuthenticatedRequest={withAuthenticatedRequest}
      onLogout={logout}
    />
  );
}
