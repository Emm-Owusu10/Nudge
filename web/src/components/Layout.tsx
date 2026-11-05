import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout({ title, children }: { title: string; children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleSignOut() {
    logout();
    navigate("/signin", { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <strong>Nudge</strong>
          <span className="header-title">{title}</span>
        </div>
        <div className="header-user">
          <span>{user?.username}</span>
          <button className="button secondary" onClick={handleSignOut}>
            Sign out
          </button>
        </div>
      </header>
      <main className="page">{children}</main>
    </div>
  );
}