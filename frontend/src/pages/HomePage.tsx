import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function HomePage() {
  const { me, loading } = useAuth();

  if (loading) return null;
  if (!me) return <Navigate to="/login" replace />;
  if (me.role === "admin") return <Navigate to="/admin" replace />;
  if (me.role === "student") return <Navigate to="/surveys" replace />;
  return <Navigate to="/no-access" replace />;
}
