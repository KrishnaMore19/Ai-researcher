// store/useAuthStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import authService from '@/services/authService';

interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthState {
  // State
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  checkAuth: () => boolean;
  clearError: () => void;
  refreshToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial State
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      // Login
      login: async (email: string, password: string) => {
        set({ loading: true, error: null });
        try {
          console.log('Store: Starting login...');
          const response = await authService.login(email, password);
          const token = response.access_token;

          console.log('Store: Token received:', token ? 'Yes' : 'No');

          // Create user object
          const user: User = {
            id: 'temp-id',
            email: email,
            full_name: email.split('@')[0],
            is_active: true,
            is_superuser: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };

          authService.saveUser(user);

          console.log('Store: Setting authenticated state');
          set({
            user,
            token,
            isAuthenticated: true,
            loading: false,
            error: null,
          });

          console.log('Store: Login complete, isAuthenticated:', get().isAuthenticated);
        } catch (error: any) {
          console.error('Store: Login error:', error);
          set({
            loading: false,
            error: error.message || 'Login failed',
            isAuthenticated: false,
          });
          throw error;
        }
      },

      // Register
      register: async (fullName: string, email: string, password: string) => {
        set({ loading: true, error: null });
        try {
          console.log('Store: Starting registration...');
          const user = await authService.register({
            full_name: fullName,
            email,
            password,
          });

          set({
            loading: false,
            error: null,
          });

          console.log('Store: Registration complete, auto-logging in...');
          // After registration, auto-login
          await get().login(email, password);
        } catch (error: any) {
          console.error('Store: Registration error:', error);
          set({
            loading: false,
            error: error.message || 'Registration failed',
          });
          throw error;
        }
      },

      // Logout
      logout: () => {
        console.log('Store: Logging out...');
        authService.logout();
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      // Set User
      setUser: (user: User) => {
        authService.saveUser(user);
        set({ user, isAuthenticated: true });
      },

      // Check if authenticated
      checkAuth: () => {
        const isAuth = authService.isAuthenticated();
        const user = authService.getCurrentUser();
        const token = authService.getToken();

        console.log('Store: Checking auth - Token exists:', !!token, 'User exists:', !!user);

        if (isAuth && user && token) {
          set({
            user,
            token,
            isAuthenticated: true,
          });
          return true;
        }

        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
        return false;
      },

      // Clear Error
      clearError: () => {
        set({ error: null });
      },

      // Refresh Token
      refreshToken: async () => {
        try {
          const response = await authService.refreshToken();
          set({ token: response.access_token });
        } catch (error: any) {
          get().logout();
          throw error;
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);