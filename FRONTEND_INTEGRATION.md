# Frontend Integration Guide

This guide explains how to integrate `oblox-fastapi-auth` with your frontend application.

## Overview

The `oblox-fastapi-auth` package provides JWT-based authentication with access and refresh tokens. This guide covers integration patterns for React, Vue, and vanilla JavaScript applications.

## Authentication Flow

1. User signs up/logs in → Receives `access_token` and `refresh_token`
2. Store tokens securely (httpOnly cookies recommended, or localStorage)
3. Include `access_token` in Authorization header for protected routes
4. When `access_token` expires, use `refresh_token` to get a new one
5. On logout, clear tokens

## API Endpoints

### Sign Up

```http
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Social Authentication (GitHub Example)

```http
POST /auth/social/github/login
Content-Type: application/json

{
  "code": "oauth_code_from_github"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## React Integration

### 1. Install Dependencies

```bash
npm install axios
# or
yarn add axios
```

### 2. Create Auth Service

```typescript
// services/authService.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface SignupData {
  email: string;
  name: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

class AuthService {
  private getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  async signup(data: SignupData): Promise<LoginResponse> {
    const response = await axios.post<LoginResponse>(
      `${API_BASE_URL}/auth/signup`,
      data
    );
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async socialLogin(provider: string, code: string): Promise<LoginResponse> {
    const response = await axios.post<LoginResponse>(
      `${API_BASE_URL}/auth/social/${provider}/login`,
      { code }
    );
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async logout(): Promise<void> {
    this.clearTokens();
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Decode JWT token (without verification - for client-side use only)
  getTokenPayload(): any {
    const token = this.getAccessToken();
    if (!token) return null;

    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      return null;
    }
  }
}

export const authService = new AuthService();
```

### 3. Create Auth Context

```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

interface AuthContextType {
  user: any | null;
  isAuthenticated: boolean;
  signup: (data: { email: string; name: string; password: string }) => Promise<void>;
  socialLogin: (provider: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated on mount
    if (authService.isAuthenticated()) {
      const payload = authService.getTokenPayload();
      setUser(payload);
    }
    setLoading(false);
  }, []);

  const signup = async (data: { email: string; name: string; password: string }) => {
    await authService.signup(data);
    const payload = authService.getTokenPayload();
    setUser(payload);
  };

  const socialLogin = async (provider: string, code: string) => {
    await authService.socialLogin(provider, code);
    const payload = authService.getTokenPayload();
    setUser(payload);
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        signup,
        socialLogin,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### 4. Create Axios Interceptor

```typescript
// utils/axiosConfig.ts
import axios from 'axios';
import { authService } from '../services/authService';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const headers = authService.getAuthHeaders();
    if (headers.Authorization) {
      config.headers.Authorization = headers.Authorization;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          // Implement refresh token endpoint call here
          // const response = await axios.post('/auth/refresh', { refresh_token: refreshToken });
          // authService.setTokens(response.data.access_token, response.data.refresh_token);
          // originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          // return api(originalRequest);
        } catch (refreshError) {
          authService.logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

### 5. Usage Example

```typescript
// components/SignupForm.tsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export const SignupForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const { signup } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await signup({ email, name, password });
      // Redirect to dashboard or show success message
    } catch (error) {
      // Handle error
      console.error('Signup failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Sign Up</button>
    </form>
  );
};
```

## Vue.js Integration

### 1. Create Auth Service

```typescript
// services/authService.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class AuthService {
  private getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  async signup(data: { email: string; name: string; password: string }) {
    const response = await axios.post(`${API_BASE_URL}/auth/signup`, data);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async socialLogin(provider: string, code: string) {
    const response = await axios.post(
      `${API_BASE_URL}/auth/social/${provider}/login`,
      { code }
    );
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

export const authService = new AuthService();
```

### 2. Create Auth Composable

```typescript
// composables/useAuth.ts
import { ref, computed } from 'vue';
import { authService } from '../services/authService';

const user = ref<any | null>(null);
const loading = ref(false);

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value);

  const signup = async (data: { email: string; name: string; password: string) => {
    loading.value = true;
    try {
      await authService.signup(data);
      // Update user state
    } catch (error) {
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const logout = () => {
    authService.logout();
    user.value = null;
  };

  return {
    user,
    isAuthenticated,
    signup,
    logout,
    loading,
  };
}
```

## GitHub OAuth Integration

### 1. Setup GitHub OAuth App

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:3000/auth/github/callback`
4. Copy Client ID and Client Secret

### 2. Add Provider to Backend

```bash
oblox-fastapi-auth-cli add-social-provider github \
  --client-id YOUR_GITHUB_CLIENT_ID \
  --client-secret YOUR_GITHUB_CLIENT_SECRET
```

### 3. Frontend Implementation

```typescript
// Redirect to GitHub OAuth
const handleGitHubLogin = () => {
  const clientId = 'YOUR_GITHUB_CLIENT_ID';
  const redirectUri = encodeURIComponent('http://localhost:3000/auth/github/callback');
  const scope = 'user:email';
  
  window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
};

// Handle callback
const handleGitHubCallback = async (code: string) => {
  try {
    await authService.socialLogin('github', code);
    // Redirect to dashboard
  } catch (error) {
    console.error('GitHub login failed:', error);
  }
};
```

## Security Best Practices

1. **Store tokens securely**: Use httpOnly cookies when possible, or localStorage with XSS protection
2. **HTTPS only**: Always use HTTPS in production
3. **Token expiration**: Implement automatic token refresh
4. **CSRF protection**: Use CSRF tokens for state-changing operations
5. **Validate tokens**: Always validate tokens on the backend
6. **Secure password storage**: Never store passwords in plain text (handled by backend)

## Error Handling

```typescript
try {
  await authService.signup({ email, name, password });
} catch (error: any) {
  if (error.response?.status === 400) {
    // Handle validation errors
    const message = error.response.data.detail;
    console.error('Validation error:', message);
  } else if (error.response?.status === 401) {
    // Handle authentication errors
    console.error('Authentication failed');
  } else {
    // Handle other errors
    console.error('Unexpected error:', error);
  }
}
```

## Example: Protected Route Component

```typescript
// components/ProtectedRoute.tsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
```

## Testing

```typescript
// Example test with Jest
import { authService } from './services/authService';

describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should sign up user and store tokens', async () => {
    const mockResponse = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
    };

    // Mock axios
    jest.spyOn(axios, 'post').mockResolvedValue({ data: mockResponse });

    await authService.signup({
      email: 'test@example.com',
      name: 'Test User',
      password: 'password123',
    });

    expect(localStorage.getItem('access_token')).toBe('mock-access-token');
    expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token');
  });
});
```

## Next Steps

- Implement token refresh endpoint
- Add password reset functionality
- Implement email verification flow
- Add multi-factor authentication (MFA)
- Implement session management
