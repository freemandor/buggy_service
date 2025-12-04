import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import logo from "../assets/clubmed_logo.png";

const NavBar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <nav
      style={{
        background: "#ffffff",
        borderBottom: "1px solid #e5e7eb",
        padding: "1rem 1.5rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <img 
          src={logo} 
          alt="Club Med" 
          style={{ height: 48, width: "auto" }} 
        />
        <div style={{ fontWeight: 700, fontSize: "1.25rem", color: "var(--brand-blue)", letterSpacing: "-0.01em" }}>
          Club Med Seychelles<br/>
          <span style={{ fontSize: "1.1rem" }}>Buggy Service</span>
        </div>
      </div>
      <div style={{ display: "flex", gap: "1.25rem", alignItems: "center" }}>
        {user && (
          <>
            {user.role === "DISPATCHER" && (
              <Link to="/dispatcher" style={{ color: "var(--brand-blue)", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
                Dispatcher
              </Link>
            )}
            {user.role === "DRIVER" && (
              <Link to="/driver" style={{ color: "var(--brand-blue)", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
                Driver
              </Link>
            )}
            {user.role === "MANAGER" && (
              <Link to="/manager" style={{ color: "var(--brand-blue)", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
                Manager
              </Link>
            )}
          </>
        )}
        {user ? (
          <>
            <span style={{ fontSize: "0.9rem", color: "#374151", fontWeight: 500 }}>
              {user.username} <span style={{ color: "#9ca3af" }}>({user.role})</span>
            </span>
            <button
              onClick={logout}
              style={{
                border: "none",
                background: "var(--brand-blue)",
                color: "white",
                padding: "0.5rem 1rem",
                cursor: "pointer",
                borderRadius: "8px",
                fontSize: "0.85rem",
                fontWeight: 600,
              }}
            >
              Logout
            </button>
          </>
        ) : (
          <Link to="/login" style={{ color: "var(--brand-blue)", textDecoration: "none", fontWeight: 600 }}>
            Login
          </Link>
        )}
      </div>
    </nav>
  );
};

export default NavBar;
