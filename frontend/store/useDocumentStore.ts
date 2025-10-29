// store/useDocumentStore.ts
import { create } from 'zustand';
import documentService from '@/services/documentService';

interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  status: string;
  uploaded_date: string;
  is_active: boolean;
}

interface DocumentState {
  // State
  documents: Document[];
  selectedDocument: Document | null;
  searchResults: any[];
  loading: boolean;
  uploading: boolean;
  error: string | null;
  filters: {
    type: string | null;
    status: string | null;
    searchQuery: string;
  };

  // Actions
  fetchDocuments: (skip?: number, limit?: number) => Promise<void>;
  uploadDocument: (file: File, title: string) => Promise<Document>;
  getDocument: (id: string) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  selectDocument: (document: Document | null) => void;
  searchDocuments: (query: string, options?: any) => Promise<void>;
  clearSearch: () => void;
  setFilter: (key: string, value: any) => void;
  clearFilters: () => void;
  clearError: () => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  // Initial State
  documents: [],
  selectedDocument: null,
  searchResults: [],
  loading: false,
  uploading: false,
  error: null,
  filters: {
    type: null,
    status: null,
    searchQuery: '',
  },

  // Fetch Documents
  fetchDocuments: async (skip = 0, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const documents = await documentService.getDocuments(skip, limit);
      set({ documents, loading: false });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to fetch documents' });
    }
  },

  // Upload Document
  uploadDocument: async (file: File, title: string) => {
    set({ uploading: true, error: null });
    try {
      const document = await documentService.uploadDocument(file, title);
      set((state) => ({
        documents: [document, ...state.documents],
        uploading: false,
      }));
      return document;
    } catch (error: any) {
      set({ uploading: false, error: error.message || 'Upload failed' });
      throw error;
    }
  },

  // Get Single Document
  getDocument: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const document = await documentService.getDocument(id);
      set({ selectedDocument: document, loading: false });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to fetch document' });
    }
  },

  // Delete Document
  deleteDocument: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await documentService.deleteDocument(id);
      set((state) => ({
        documents: state.documents.filter((doc) => doc.id !== id),
        selectedDocument: state.selectedDocument?.id === id ? null : state.selectedDocument,
        loading: false,
      }));
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to delete document' });
      throw error;
    }
  },

  // Select Document
  selectDocument: (document: Document | null) => {
    set({ selectedDocument: document });
  },

  // Search Documents
  searchDocuments: async (query: string, options = {}) => {
    set({ loading: true, error: null });
    try {
      const result = await documentService.searchDocuments({
        query,
        ...options,
      });
      set({
        searchResults: result.data,
        loading: false,
        filters: { ...get().filters, searchQuery: query },
      });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Search failed' });
    }
  },

  // Clear Search
  clearSearch: () => {
    set({
      searchResults: [],
      filters: { ...get().filters, searchQuery: '' },
    });
  },

  // Set Filter
  setFilter: (key: string, value: any) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    }));
  },

  // Clear Filters
  clearFilters: () => {
    set({
      filters: {
        type: null,
        status: null,
        searchQuery: '',
      },
    });
  },

  // Clear Error
  clearError: () => {
    set({ error: null });
  },
}));