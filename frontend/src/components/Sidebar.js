import React from 'react';
import { NavLink } from 'react-router-dom';
import { FiLink, FiSearch, FiCpu } from 'react-icons/fi';
import './Sidebar.css'; // Import a dedicated CSS file for the sidebar

const Sidebar = () => (
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
      <NavLink 
        to="/topic-search" 
        className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
      >
        <FiSearch className="nav-icon" />
        <span>Topic Synthesis</span>
      </NavLink>
    </nav>
  </aside>
);

export default Sidebar;