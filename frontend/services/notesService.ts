// services/notesService.ts
import api from './api';
import { config } from '@/lib/config';

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

interface NoteCreate {
  title: string;
  content: string;
  tags?: string[];
  is_pinned?: boolean;
  document_id?: string;
}

interface NoteUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  is_pinned?: boolean;
}

class NotesService {
  /**
   * Check if notes feature is enabled
   */
  private checkFeatureEnabled(): void {
    if (!config.features.notes) {
      throw new Error('Notes feature is disabled');
    }
  }

  /**
   * Create a new note
   */
  async createNote(noteData: NoteCreate): Promise<Note> {
    this.checkFeatureEnabled();

    const response = await api.post<Note>('/notes/', noteData);
    return response.data;
  }

  /**
   * Get all notes with optional filters
   */
  async getNotes(
    documentId?: string,
    skip: number = 0,
    limit: number = config.pagination.notesPerPage
  ): Promise<Note[]> {
    this.checkFeatureEnabled();

    const params: any = { skip, limit };
    if (documentId) {
      params.document_id = documentId;
    }

    const response = await api.get<Note[]>('/notes/', { params });
    return response.data;
  }

  /**
   * Get a single note by ID
   */
  async getNote(noteId: string): Promise<Note> {
    this.checkFeatureEnabled();

    const response = await api.get<Note>(`/notes/${noteId}`);
    return response.data;
  }

  /**
   * Update an existing note
   */
  async updateNote(noteId: string, noteData: NoteUpdate): Promise<Note> {
    this.checkFeatureEnabled();

    const response = await api.put<Note>(`/notes/${noteId}`, noteData);
    return response.data;
  }

  /**
   * Delete a note
   */
  async deleteNote(noteId: string): Promise<{ detail: string }> {
    this.checkFeatureEnabled();

    const response = await api.delete<{ detail: string }>(`/notes/${noteId}`);
    return response.data;
  }

  /**
   * Toggle pin status of a note
   */
  async togglePin(noteId: string, isPinned: boolean): Promise<Note> {
    this.checkFeatureEnabled();

    const response = await api.put<Note>(`/notes/${noteId}`, {
      is_pinned: isPinned,
    });
    return response.data;
  }

  /**
   * Search notes by content or title (client-side)
   */
  searchNotes(notes: Note[], searchTerm: string): Note[] {
    const term = searchTerm.toLowerCase();
    return notes.filter(
      (note) =>
        note.title.toLowerCase().includes(term) ||
        note.content.toLowerCase().includes(term) ||
        note.tags.some((tag) => tag.toLowerCase().includes(term))
    );
  }

  /**
   * Filter notes by tags (client-side)
   */
  filterByTags(notes: Note[], tags: string[]): Note[] {
    if (tags.length === 0) return notes;
    return notes.filter((note) =>
      tags.some((tag) => note.tags.includes(tag))
    );
  }

  /**
   * Get pinned notes (client-side)
   */
  getPinnedNotes(notes: Note[]): Note[] {
    return notes.filter((note) => note.is_pinned);
  }

  /**
   * Get all unique tags from notes (client-side)
   */
  getAllTags(notes: Note[]): string[] {
    const tagsSet = new Set<string>();
    notes.forEach((note) => {
      note.tags.forEach((tag) => tagsSet.add(tag));
    });
    return Array.from(tagsSet).sort();
  }

  /**
   * Filter notes by document (client-side)
   */
  filterByDocument(notes: Note[], documentId: string): Note[] {
    return notes.filter((note) => note.document_id === documentId);
  }
}

export default new NotesService();