import React from "react";
import NavBar from "./NavBar";

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="app-shell">
      <NavBar />
      <main>{children}</main>
    </div>
  );
};

export default Layout;
