import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Loader from "../components/Loader";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: Array<"DRIVER" | "DISPATCHER" | "MANAGER">;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <Loader />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    if (user.role === "DISPATCHER") return <Navigate to="/dispatcher" replace />;
    if (user.role === "DRIVER") return <Navigate to="/driver" replace />;
    if (user.role === "MANAGER") return <Navigate to="/manager" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

