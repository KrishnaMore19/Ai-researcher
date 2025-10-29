// store/useNotesStore.ts
import { create } from 'zustand';
import notesService from '@/services/notesService';

interface Note {
  id: string;
  user_id: string;
  title: string;
  content: string;
  tags: string[];
  is_pinned: boolean;
  document_id?: string;
  created_at: string;
  updated_at: string;
}

interface NotesState {
  // State
  notes: Note[];
  selectedNote: Note | null;
  loading: boolean;
  error: string | null;
  filters: {
    documentId: string | null;
    tags: string[];
    searchQuery: string;
  };

  // Actions
  fetchNotes: (documentId?: string, skip?: number, limit?: number) => Promise<void>;
  createNote: (title: string, content: string, tags?: string[], documentId?: string) => Promise<Note>;
  updateNote: (id: string, data: Partial<Note>) => Promise<void>;
  deleteNote: (id: string) => Promise<void>;
  getNote: (id: string) => Promise<void>;
  selectNote: (note: Note | null) => void;
  togglePin: (id: string) => Promise<void>;
  searchNotes: (query: string) => void;
  filterByTags: (tags: string[]) => void;
  clearFilters: () => void;
  clearError: () => void;
}

export const useNotesStore = create<NotesState>((set, get) => ({
  // Initial State
  notes: [],
  selectedNote: null,
  loading: false,
  error: null,
  filters: {
    documentId: null,
    tags: [],
    searchQuery: '',
  },

  // Fetch Notes
  fetchNotes: async (documentId?: string, skip = 0, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const notes = await notesService.getNotes(documentId, skip, limit);
      set({ notes, loading: false });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to fetch notes' });
    }
  },

  // Create Note
  createNote: async (title: string, content: string, tags = [], documentId?: string) => {
    set({ loading: true, error: null });
    try {
      const note = await notesService.createNote({
        title,
        content,
        tags,
        is_pinned: false,
        document_id: documentId,
      });
      set((state) => ({
        notes: [note, ...state.notes],
        loading: false,
      }));
      return note;
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to create note' });
      throw error;
    }
  },

  // Update Note
  updateNote: async (id: string, data: Partial<Note>) => {
    set({ loading: true, error: null });
    try {
      const updatedNote = await notesService.updateNote(id, data);
      set((state) => ({
        notes: state.notes.map((note) => (note.id === id ? updatedNote : note)),
        selectedNote: state.selectedNote?.id === id ? updatedNote : state.selectedNote,
        loading: false,
      }));
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to update note' });
      throw error;
    }
  },

  // Delete Note
  deleteNote: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await notesService.deleteNote(id);
      set((state) => ({
        notes: state.notes.filter((note) => note.id !== id),
        selectedNote: state.selectedNote?.id === id ? null : state.selectedNote,
        loading: false,
      }));
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to delete note' });
      throw error;
    }
  },

  // Get Single Note
  getNote: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const note = await notesService.getNote(id);
      set({ selectedNote: note, loading: false });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to fetch note' });
    }
  },

  // Select Note
  selectNote: (note: Note | null) => {
    set({ selectedNote: note });
  },

  // Toggle Pin
  togglePin: async (id: string) => {
    const note = get().notes.find((n) => n.id === id);
    if (!note) return;

    set({ loading: true, error: null });
    try {
      const updatedNote = await notesService.togglePin(id, !note.is_pinned);
      set((state) => ({
        notes: state.notes.map((n) => (n.id === id ? updatedNote : n)),
        loading: false,
      }));
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to toggle pin' });
      throw error;
    }
  },

  // Search Notes (Local)
  searchNotes: (query: string) => {
    set((state) => ({
      filters: { ...state.filters, searchQuery: query },
    }));
  },

  // Filter By Tags (Local)
  filterByTags: (tags: string[]) => {
    set((state) => ({
      filters: { ...state.filters, tags },
    }));
  },

  // Clear Filters
  clearFilters: () => {
    set({
      filters: {
        documentId: null,
        tags: [],
        searchQuery: '',
      },
    });
  },

  // Clear Error
  clearError: () => {
    set({ error: null });
  },
}));