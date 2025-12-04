import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import logo from "../assets/clubmed_logo.png";

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app-shell">
      <div style={{ maxWidth: 400, margin: "4rem auto", padding: "1rem" }}>
        <div className="card">
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: "2rem" }}>
            <img 
              src={logo} 
              alt="Club Med" 
              style={{ height: 64, width: "auto", marginBottom: "1rem" }} 
            />
            <div style={{ 
              fontWeight: 700, 
              fontSize: "1.5rem", 
              color: "var(--brand-blue)", 
              textAlign: "center",
              lineHeight: 1.3,
              letterSpacing: "-0.01em"
            }}>
              Club Med Seychelles
              <br/>
              <span style={{ fontSize: "1.25rem" }}>Buggy Service</span>
            </div>
          </div>

          {error && <div className="banner-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label className="form-label">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="form-input"
              />
            </div>
            <div className="form-field">
              <label className="form-label">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-input"
              />
            </div>
            <button type="submit" disabled={submitting} className="primary-button" style={{ width: "100%", marginTop: "0.5rem" }}>
              {submitting ? "Logging in..." : "Login"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
