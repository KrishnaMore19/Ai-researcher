// store/middleware.ts
import { StateStorage } from 'zustand/middleware';

// Custom storage that handles SSR (Server-Side Rendering) for Next.js
export const createStorage = (): StateStorage => {
  // Check if we're in a browser environment
  if (typeof window === 'undefined') {
    return {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {},
    };
  }

  return {
    getItem: (name: string) => {
      try {
        const item = localStorage.getItem(name);
        return item;
      } catch (error) {
        console.error(`Error getting item ${name} from localStorage:`, error);
        return null;
      }
    },
    setItem: (name: string, value: string) => {
      try {
        localStorage.setItem(name, value);
      } catch (error) {
        console.error(`Error setting item ${name} to localStorage:`, error);
      }
    },
    removeItem: (name: string) => {
      try {
        localStorage.removeItem(name);
      } catch (error) {
        console.error(`Error removing item ${name} from localStorage:`, error);
      }
    },
  };
};

// Custom persist options
export const persistOptions = {
  storage: createStorage(),
};

// Helper to clear all persisted stores
export const clearAllStores = () => {
  if (typeof window === 'undefined') return;

  const storeKeys = [
    'auth-storage',
    'ui-storage',
  ];

  storeKeys.forEach((key) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error clearing store ${key}:`, error);
    }
  });
};

// Helper to check if store is hydrated
export const isStoreHydrated = (storeName: string): boolean => {
  if (typeof window === 'undefined') return false;

  try {
    return localStorage.getItem(storeName) !== null;
  } catch (error) {
    return false;
  }
};