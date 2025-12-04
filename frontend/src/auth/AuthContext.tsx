import React, { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, getCurrentUser, logout as apiLogout, User } from "../api/auth";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      try {
        const u = await getCurrentUser();
        setUser(u);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const handleLogin = async (username: string, password: string) => {
    const u = await apiLogin(username, password);
    setUser(u);
  };

  const handleLogout = () => {
    apiLogout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login: handleLogin, logout: handleLogout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

