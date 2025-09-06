import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_BASE = '/api';

  useEffect(() => {
    // Check localStorage on mount
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      fetchCurrentUser(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchCurrentUser = async (authToken = token) => {
    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (phoneOrEmail, password) => {
    try {
      setLoading(true);
      
      // Determine if input is email or phone
      const isEmail = phoneOrEmail.includes('@');
      const requestData = isEmail 
        ? { email: phoneOrEmail, password }
        : { phone: phoneOrEmail, password };
      
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (response.ok) {
        // Store token first
        localStorage.setItem('token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }
        
        // Update state immediately
        setToken(data.access_token);
        setUser(data.user);
        
        return { success: true, user: data.user };
      } else {
        return { success: false, error: data.error || 'Ошибка входа' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Ошибка сети' };
    } finally {
      setLoading(false);
    }
  };

  const register = async (phone, password, email = null) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ phone, password, email })
      });

      const data = await response.json();

      if (response.ok) {
        // Store token first
        localStorage.setItem('token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }
        
        // Update state immediately
        setToken(data.access_token);
        setUser(data.user);
        
        return { success: true, user: data.user, message: data.message };
      } else {
        return { 
          success: false, 
          error: data.error || 'Ошибка регистрации',
          error_code: data.error_code,
          field: data.field,
          message: data.message
        };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: 'Ошибка сети' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
  };

  const apiCall = async (url, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers
      });

      if (response.status === 401) {
        logout();
        throw new Error('Unauthorized');
      }

      return response;
    } catch (error) {
      console.error('API call error:', error);
      throw error;
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    apiCall,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

