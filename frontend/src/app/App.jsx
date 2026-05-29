import LoginView from "../features/auth/ui/LoginView";
import { useAuthSession } from "../features/auth/model/useAuthSession";
import TasksPage from "../features/tasks/ui/TasksPage";

export default function App() {
  const { authUser, login, logout } = useAuthSession();

  if (!authUser) {
    return <LoginView onLogin={login} />;
  }

  return <TasksPage authUser={authUser} onLogout={logout} />;
}
