import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AuthPage.css'; // Use the new CSS file

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (isLogin) {
        await login(username, password);
        navigate('/'); // Redirect to home on successful login
      } else {
        await register(username, password);
        alert('Registration successful! Please log in.');
        setIsLogin(true); // Switch to login view
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setUsername('');
    setPassword('');
  };

  return (
    <div className="auth-container">
      <div className="auth-form-wrapper">
        <h2>{isLogin ? 'Login' : 'Register'}</h2>
        <form onSubmit={handleSubmit}>
          {error && <p className="error-message">{error}</p>}
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="submit-btn">
            {isLogin ? 'Login' : 'Register'}
          </button>
          
          {isLogin && (
            <>
              <div style={{ textAlign: 'center', margin: '1rem 0', color: '#888' }}>OR</div>
              <a href={`${API_BASE_URL}/api/login/google`} className="submit-btn google-btn">
                Sign in with Google
              </a>
            </>
          )}

          <p className="toggle-auth" onClick={toggleMode}>
            {isLogin ? "Don't have an account? Register" : 'Already have an account? Login'}
          </p>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;
