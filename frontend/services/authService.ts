// services/authService.ts
import api from './api';
import { config } from '@/lib/config';

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

class AuthService {
  /**
   * Login user with email and password
   */
  async login(email: string, password: string): Promise<TokenResponse> {
    // Backend expects OAuth2 form data format
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post<TokenResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    // Save token using config key
    if (response.data.access_token && typeof window !== 'undefined') {
      localStorage.setItem(config.tokenKey, response.data.access_token);
    }

    return response.data;
  }

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  }

  /**
   * Logout user - clear local storage
   */
  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(config.tokenKey);
      localStorage.removeItem(config.refreshTokenKey);
      localStorage.removeItem(config.userKey);
      window.location.href = '/login';
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/refresh');
    
    if (response.data.access_token && typeof window !== 'undefined') {
      localStorage.setItem(config.tokenKey, response.data.access_token);
    }
    
    return response.data;
  }

  /**
   * Get current user from localStorage
   */
  getCurrentUser(): User | null {
    if (typeof window === 'undefined') return null;

    const userData = localStorage.getItem(config.userKey);
    if (userData) {
      try {
        return JSON.parse(userData);
      } catch (error) {
        console.error('Error parsing user data:', error);
        return null;
      }
    }
    return null;
  }

  /**
   * Save user data to localStorage
   */
  saveUser(user: User): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(config.userKey, JSON.stringify(user));
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    const token = localStorage.getItem(config.tokenKey);
    return !!token;
  }

  /**
   * Get auth token
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(config.tokenKey);
  }
}

export default new AuthService();