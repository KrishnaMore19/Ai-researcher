// types/chat.ts

export interface ChatMessage {
  id: string;
  session_id?: string;
  sender: 'user' | 'ai';
  content: string;
  created_at: string;
  attachments?: string[];
}

export interface ChatRequest {
  message: string;
  document_ids?: string[];
  model_name?: string;
}

export interface ChatResponse {
  id: string;
  session_id?: string;
  sender: string;
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title?: string;
  created_at: string;
  updated_at?: string;
}

export interface SummarizeRequest {
  document_ids: string[];
  summary_type?: 'short' | 'detailed' | 'bullet' | 'section';
  model_name?: string;
}

export interface SummarizeResponse {
  success: boolean;
  summary: string;
  summary_type: string;
  document_count: number;
}

export interface ModelSelectionResponse {
  success: boolean;
  selected_model: string;
  model_name: string;
  strengths: string[];
  reason: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  strengths: string[];
  bestFor: string[];
}

export type SearchMode = 'semantic' | 'hybrid' | 'keyword';

export interface ChatState {
  messages: ChatMessage[];
  currentMessage: string;
  selectedModel: string;
  selectedDocuments: string[];
  loading: boolean;
  streaming: boolean;
  error: string | null;
  searchMode: SearchMode;
}