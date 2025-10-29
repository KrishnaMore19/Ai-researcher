// store/useUIStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

interface Modal {
  [key: string]: boolean;
}

interface UIState {
  // State
  sidebarOpen: boolean;
  modals: Modal;
  toasts: Toast[];
  globalLoading: boolean;
  theme: 'light' | 'dark';

  // Sidebar Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Modal Actions
  openModal: (name: string) => void;
  closeModal: (name: string) => void;
  isModalOpen: (name: string) => boolean;

  // Toast Actions
  showToast: (message: string, type?: 'success' | 'error' | 'warning' | 'info', duration?: number) => void;
  hideToast: (id: string) => void;
  clearToasts: () => void;

  // Loading Actions
  setGlobalLoading: (loading: boolean) => void;

  // Theme Actions
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      // Initial State
      sidebarOpen: true,
      modals: {},
      toasts: [],
      globalLoading: false,
      theme: 'light',

      // Toggle Sidebar
      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }));
      },

      // Set Sidebar Open
      setSidebarOpen: (open: boolean) => {
        set({ sidebarOpen: open });
      },

      // Open Modal
      openModal: (name: string) => {
        set((state) => ({
          modals: { ...state.modals, [name]: true },
        }));
      },

      // Close Modal
      closeModal: (name: string) => {
        set((state) => ({
          modals: { ...state.modals, [name]: false },
        }));
      },

      // Check if Modal is Open
      isModalOpen: (name: string) => {
        return get().modals[name] || false;
      },

      // Show Toast
      showToast: (message: string, type = 'info' as const, duration = 5000) => {
        const id = `toast-${Date.now()}-${Math.random()}`;
        const toast: Toast = { id, message, type, duration };

        set((state) => ({
          toasts: [...state.toasts, toast],
        }));

        // Auto-hide after duration
        if (duration > 0) {
          setTimeout(() => {
            get().hideToast(id);
          }, duration);
        }
      },

      // Hide Toast
      hideToast: (id: string) => {
        set((state) => ({
          toasts: state.toasts.filter((toast) => toast.id !== id),
        }));
      },

      // Clear All Toasts
      clearToasts: () => {
        set({ toasts: [] });
      },

      // Set Global Loading
      setGlobalLoading: (loading: boolean) => {
        set({ globalLoading: loading });
      },

      // Toggle Theme
      toggleTheme: () => {
        set((state) => ({
          theme: state.theme === 'light' ? 'dark' : 'light',
        }));

        // Apply theme to document
        const newTheme = get().theme;
        document.documentElement.classList.toggle('dark', newTheme === 'dark');
      },

      // Set Theme
      setTheme: (theme: 'light' | 'dark') => {
        set({ theme });
        document.documentElement.classList.toggle('dark', theme === 'dark');
      },
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
      }),
    }
  )
);