// store/useAnalyticsStore.ts
import { create } from 'zustand';
import analyticsService from '@/services/analyticsService';

interface AnalyticsSummary {
  total_documents: number;
  total_queries: number;
  successful_queries: number;
  query_success_rate: number;
  productivity_score: number;
}

interface Analytics {
  id: string;
  user_id: string;
  total_documents: number;
  total_queries: number;
  successful_queries: number;
  productivity_score: number;
  document_uploads: any[];
  document_views: any[];
  query_history: any[];
  top_documents: any[];
  created_at: string;
  updated_at: string;
}

interface AnalyticsState {
  // State
  analytics: Analytics | null;
  summary: AnalyticsSummary | null;
  loading: boolean;
  error: string | null;
  dateRange: {
    start: string | null;
    end: string | null;
  };

  // Actions
  fetchAnalytics: (skip?: number, limit?: number) => Promise<void>;
  fetchSummary: () => Promise<void>;
  logDocumentUpload: (documentId: string, documentName: string) => Promise<void>;
  logDocumentView: (documentId: string, documentName: string) => Promise<void>;
  logAIQuery: (modelName: string, query: string, response: string, success?: boolean) => Promise<void>;
  setDateRange: (start: string, end: string) => void;
  clearDateRange: () => void;
  clearError: () => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  // Initial State
  analytics: null,
  summary: null,
  loading: false,
  error: null,
  dateRange: {
    start: null,
    end: null,
  },

  // Fetch Full Analytics
  fetchAnalytics: async (skip = 0, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const analytics = await analyticsService.getAnalytics(skip, limit);
      set({ analytics, loading: false });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to fetch analytics' });
    }
  },

  // Fetch Summary for Dashboard
  fetchSummary: async () => {
    set({ loading: true, error: null });
    try {
      const summary = await analyticsService.getSummary();
      set({ summary, loading: false });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to fetch summary' });
    }
  },

  // Log Document Upload
  logDocumentUpload: async (documentId: string, documentName: string) => {
    try {
      await analyticsService.logDocumentUpload(documentId, documentName);
      // Optionally refresh summary
      get().fetchSummary();
    } catch (error: any) {
      console.error('Failed to log document upload:', error);
    }
  },

  // Log Document View
  logDocumentView: async (documentId: string, documentName: string) => {
    try {
      await analyticsService.logDocumentView(documentId, documentName);
    } catch (error: any) {
      console.error('Failed to log document view:', error);
    }
  },

  // Log AI Query
  logAIQuery: async (
    modelName: string,
    query: string,
    response: string,
    success = true
  ) => {
    try {
      await analyticsService.logAIQuery(modelName, query, response, success);
      // Optionally refresh summary
      get().fetchSummary();
    } catch (error: any) {
      console.error('Failed to log AI query:', error);
    }
  },

  // Set Date Range
  setDateRange: (start: string, end: string) => {
    set({
      dateRange: { start, end },
    });
  },

  // Clear Date Range
  clearDateRange: () => {
    set({
      dateRange: { start: null, end: null },
    });
  },

  // Clear Error
  clearError: () => {
    set({ error: null });
  },
}));