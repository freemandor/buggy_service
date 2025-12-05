import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import logo from "../assets/clubmed_logo.png";

const NavBar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="nav-left">
        <img src={logo} alt="Club Med" className="nav-logo" />
        <div className="nav-brand">
          Club Med Seychelles
          <br />
          <span>Buggy Service</span>
        </div>
      </div>
      <div className="nav-right">
        <div className="nav-links">
          {user && user.role === "DISPATCHER" && (
            <Link className="nav-link" to="/dispatcher">Dispatcher</Link>
          )}
          {user && user.role === "DRIVER" && (
            <Link className="nav-link" to="/driver">Driver</Link>
          )}
          {user && user.role === "MANAGER" && (
            <Link className="nav-link" to="/manager">Manager</Link>
          )}
        </div>
        {user ? (
          <div className="nav-user">
            <span className="nav-username">
              {user.username} <span className="nav-role">({user.role})</span>
            </span>
            <button className="nav-logout" onClick={logout}>Logout</button>
          </div>
        ) : (
          <Link className="nav-link" to="/login">Login</Link>
        )}
      </div>
    </nav>
  );
};

export default NavBar;
