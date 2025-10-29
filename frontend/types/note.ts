// types/note.ts

export interface Note {
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

export interface NoteCreate {
  title: string;
  content: string;
  tags?: string[];
  is_pinned?: boolean;
  document_id?: string;
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  is_pinned?: boolean;
}

export interface NoteFilters {
  documentId: string | null;
  tags: string[];
  searchQuery: string;
  showPinnedOnly?: boolean;
}

export interface NotesState {
  notes: Note[];
  selectedNote: Note | null;
  loading: boolean;
  error: string | null;
  filters: NoteFilters;
}