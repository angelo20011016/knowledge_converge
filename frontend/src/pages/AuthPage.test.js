import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import AuthPage from './AuthPage';

const mockLogin = jest.fn();
const mockRegister = jest.fn();

const renderWithContext = (component) => {
  return render(
    <AuthContext.Provider value={{ login: mockLogin, register: mockRegister }}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </AuthContext.Provider>
  );
};

describe('AuthPage', () => {
  beforeEach(() => {
    mockLogin.mockClear();
    mockRegister.mockClear();
  });

  test('renders login form by default', () => {
    renderWithContext(<AuthPage />);
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  test('toggles to register form and back', () => {
    renderWithContext(<AuthPage />);
    const toggleToRegister = screen.getByText(/don't have an account\? register/i);
    fireEvent.click(toggleToRegister);
    expect(screen.getByRole('heading', { name: /register/i })).toBeInTheDocument();

    const toggleToLogin = screen.getByText(/already have an account\? login/i);
    fireEvent.click(toggleToLogin);
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
  });

  test('calls login function on login form submission', async () => {
    renderWithContext(<AuthPage />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  test('calls register function on register form submission', async () => {
    renderWithContext(<AuthPage />);
    fireEvent.click(screen.getByText(/don't have an account\? register/i));
    
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'newuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'newpassword' } });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('newuser', 'newpassword');
    });
  });
});
