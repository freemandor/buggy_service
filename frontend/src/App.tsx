import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import DispatcherDashboard from "./pages/DispatcherDashboard";
import DriverRoutePage from "./pages/DriverRoutePage";
import ManagerDashboard from "./pages/ManagerDashboard";
import POIDetailPage from "./pages/POIDetailPage";

const App: React.FC = () => {
  const { user, loading } = useAuth();

  const HomeRedirect: React.FC = () => {
    if (!user) return <Navigate to="/login" replace />;
    if (user.role === "DISPATCHER") return <Navigate to="/dispatcher" replace />;
    if (user.role === "DRIVER") return <Navigate to="/driver" replace />;
    if (user.role === "MANAGER") return <Navigate to="/manager" replace />;
    return <Navigate to="/login" replace />;
  };

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dispatcher"
        element={
          <ProtectedRoute allowedRoles={["DISPATCHER", "MANAGER"]}>
            <DispatcherDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/driver"
        element={
          <ProtectedRoute allowedRoles={["DRIVER"]}>
            <DriverRoutePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager"
        element={
          <ProtectedRoute allowedRoles={["MANAGER"]}>
            <ManagerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager/pois/:poiId"
        element={
          <ProtectedRoute allowedRoles={["MANAGER"]}>
            <POIDetailPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<HomeRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;

