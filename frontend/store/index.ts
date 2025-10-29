// store/index.ts
// Export all stores from a single entry point

export { useAuthStore } from './useAuthStore';
export { useDocumentStore } from './useDocumentStore';
export { useChatStore } from './useChatStore';
export { useNotesStore } from './useNotesStore';
export { useAnalyticsStore } from './useAnalyticsStore';
export { useSettingsStore } from './useSettingsStore';
export { useUIStore } from './useUIStore';

// Export middleware helpers
export { createStorage, persistOptions, clearAllStores, isStoreHydrated } from './middleware';