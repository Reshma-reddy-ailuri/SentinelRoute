import React from 'react';
import { NavLink } from 'react-router-dom';
import { ShieldCheck, MessageSquare, LayoutDashboard, Shield } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <ShieldCheck className="brand-icon" size={28} />
          <div>
            <span className="brand-title">Enterprise GenAI</span>
            <span className="brand-subtitle">Security Gateway</span>
          </div>
        </div>

        <nav className="nav-links">
          <NavLink 
            to="/" 
            className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}
            end
          >
            <MessageSquare size={18} />
            <span>Employee Chat</span>
          </NavLink>

          <NavLink 
            to="/admin" 
            className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}
          >
            <LayoutDashboard size={18} />
            <span>Admin Dashboard</span>
          </NavLink>
        </nav>

        <div className="security-status-indicator">
          <Shield size={16} className="status-icon" />
          <span>Gateway Active</span>
        </div>
      </div>
    </header>
  );
}
