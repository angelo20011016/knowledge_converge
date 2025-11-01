import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { FiLink, FiCpu, FiSettings, FiLogIn, FiLogOut } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const Sidebar = ({ openTemplateModal }) => { // Receive openTemplateModal prop
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <FiCpu className="logo-icon" />
        <h1 className="logo-text">
          <span data-text="No-Ledge">No-Ledge</span>
        </h1>
      </div>
      <nav className="nav-menu">
        <NavLink 
          to="/" 
          className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
        >
          <FiLink className="nav-icon" />
          <span>Single URL Analysis</span>
        </NavLink>
        {isAuthenticated && (
          <button className="nav-item" onClick={openTemplateModal}>
            <FiSettings className="nav-icon" />
            <span>Manage Templates</span>
          </button>
        )}
      </nav>
      <div className="sidebar-footer">
        {isAuthenticated ? (
          <button onClick={handleLogout} className="nav-item logout-btn">
            <FiLogOut className="nav-icon" />
            <span>Logout</span>
          </button>
        ) : (
          <NavLink 
            to="/auth" 
            className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
          >
            <FiLogIn className="nav-icon" />
            <span>Login / Register</span>
          </NavLink>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
