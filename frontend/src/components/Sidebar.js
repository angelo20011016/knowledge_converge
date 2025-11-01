import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { FiLink, FiCpu, FiSettings, FiLogIn, FiLogOut, FiClock, FiMessageSquare, FiSearch } from 'react-icons/fi';
import './Sidebar.css'; // Import a dedicated CSS file for the sidebar
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

const Sidebar = () => {
  const [session, setSession] = useState({ logged_in: false });

  useEffect(() => {
    // Fetch session info when component mounts and on an interval
    const fetchSession = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/session`, { withCredentials: true });
        setSession(response.data);
      } catch (error) {
        console.error("Error fetching session:", error);
        setSession({ logged_in: false });
      }
    };

    fetchSession();
    const interval = setInterval(fetchSession, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const handleLogout = async () => {
    await axios.get(`${API_BASE_URL}/api/logout`, { withCredentials: true });
    window.location.reload(); // Reload to clear state
  };

  const handleFeedback = () => {
    const content = prompt("Please enter your feedback or suggestions:");
    if (content) {
      axios.post(`${API_BASE_URL}/api/feedback`, { content }, { withCredentials: true })
        .then(() => alert("Thank you for your feedback!"))
        .catch(err => alert("Failed to submit feedback. " + (err.response?.data?.error || '')));
    }
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
        <NavLink to="/" className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
          <FiLink className="nav-icon" />
          <span>URL Analysis</span>
        </NavLink>
        {/* The Topic Search functionality has been disabled as per the improvement plan. */}
        {/* <NavLink to="/topic-search" className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
          <FiSearch className="nav-icon" />
          <span>Topic Search</span>
        </NavLink> */}
        {session.logged_in && (
          <>
            <NavLink to="/history" className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
              <FiClock className="nav-icon" />
              <span>History</span>
            </NavLink>
            <NavLink to="/templates" className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
              <FiSettings className="nav-icon" />
              <span>Templates</span>
            </NavLink>
          </>
        )}
      </nav>
      <div className="sidebar-footer">
        {session.logged_in ? (
          <div className="user-profile">
            <img src={session.user.picture} alt={session.user.name} className="profile-pic" />
            <div className="user-info">
              <span className="user-name">{session.user.name}</span>
              <span className="user-quota">Usage: {session.usage.used} / {session.usage.quota} per day</span>
            </div>
            <button onClick={handleLogout} className="logout-button" title="Logout"><FiLogOut /></button>
          </div>
        ) : (
          <>
            <a href={`${API_BASE_URL}/api/login`} className="nav-item login-btn">
              <FiLogIn className="nav-icon" />
              <span>Login with Google</span>
            </a>
            <span className="login-prompt">Login for 5 uses per day.</span>
          </>
        )}
        <div className="nav-item feedback-btn" onClick={handleFeedback}>
          <FiMessageSquare className="nav-icon" />
          <span>Feedback</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;