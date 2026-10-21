import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { homePathFor } from "./auth/roles";
import type { Role } from "./types";
import AdminDashboard from "./pages/AdminDashboard";
import AdvisorDashboard from "./pages/AdvisorDashboard";
import LecturerDashboard from "./pages/LecturerDashboard";
import SignIn from "./pages/SignIn";
import StudentDetail from "./pages/StudentDetail";

// Hides a page from users whose role isn't allowed. This is only for navigation.
// The API checks every request again, so a hidden page cannot bypass the rules.
function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user, ready } = useAuth();
  if (!ready) return <p className="muted page">Loading…</p>;
  if (!user) return <Navigate to="/signin" replace />;
  if (!roles.includes(user.role)) return <Navigate to={homePathFor(user.role)} replace />;
  return <>{children}</>;
}

function HomeRedirect() {
  const { user, ready } = useAuth();
  if (!ready) return <p className="muted page">Loading…</p>;
  return <Navigate to={user ? homePathFor(user.role) : "/signin"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/signin" element={<SignIn />} />
      <Route
        path="/advisor"
        element={
          <RequireRole roles={["advisor"]}>
            <AdvisorDashboard />
          </RequireRole>
        }
      />
      <Route
        path="/advisor/students/:id"
        element={
          <RequireRole roles={["advisor"]}>
            <StudentDetail />
          </RequireRole>
        }
      />
      <Route
        path="/lecturer"
        element={
          <RequireRole roles={["lecturer"]}>
            <LecturerDashboard />
          </RequireRole>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireRole roles={["administrator"]}>
            <AdminDashboard />
          </RequireRole>
        }
      />
      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  );
}