import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../api/types";

export function ProtectedRoute({
  role,
  children,
}: {
  role: Role;
  children: React.ReactNode;
}) {
  const { me, loading } = useAuth();

  if (loading) {
    return <div className="flex justify-center py-20 text-gray-500">불러오는 중...</div>;
  }

  if (!me) {
    return <Navigate to="/login" replace />;
  }

  if (me.role === "unregistered") {
    return <Navigate to="/no-access" replace />;
  }

  if (me.role !== role) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
