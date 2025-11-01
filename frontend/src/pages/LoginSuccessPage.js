import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LoginSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setAuthToken } = useAuth();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setAuthToken(token);
      navigate('/');
    } else {
      // Handle error or case where token is not present
      console.error("No token found after SSO redirect.");
      navigate('/login');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  return (
    <div style={{ textAlign: 'center', marginTop: '5rem' }}>
      <h2>Logging you in...</h2>
      <p>Please wait while we redirect you.</p>
    </div>
  );
};

export default LoginSuccessPage;
