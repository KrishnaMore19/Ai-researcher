// store/useChatStore.ts
import { create } from 'zustand';
import chatService from '@/services/chatService';

interface ChatMessage {
  id: string;
  session_id?: string;
  sender: 'user' | 'ai';
  content: string;
  created_at: string;
}

interface ChatState {
  // State
  messages: ChatMessage[];
  currentMessage: string;
  selectedModel: string;
  selectedDocuments: string[];
  loading: boolean;
  streaming: boolean;
  error: string | null;
  searchMode: 'semantic' | 'hybrid' | 'keyword';

  // Actions
  sendMessage: (message: string, documentIds?: string[]) => Promise<void>;
  fetchHistory: (skip?: number, limit?: number) => Promise<void>;
  deleteMessage: (id: string) => Promise<void>;
  clearChat: () => void;
  setCurrentMessage: (message: string) => void;
  setModel: (model: string) => void;
  setDocuments: (documentIds: string[]) => void;
  setSearchMode: (mode: 'semantic' | 'hybrid' | 'keyword') => void;
  autoSelectModel: (query: string) => Promise<void>;
  summarizeDocuments: (documentIds: string[], type?: string) => Promise<string>;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial State
  messages: [],
  currentMessage: '',
  selectedModel: 'llama',
  selectedDocuments: [],
  loading: false,
  streaming: false,
  error: null,
  searchMode: 'semantic',

  // Send Message
  sendMessage: async (message: string, documentIds?: string[]) => {
    set({ loading: true, error: null });

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      sender: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
    }));

    try {
      const response = await chatService.sendMessage(
        message,
        documentIds || get().selectedDocuments,
        get().selectedModel,
        get().searchMode,
        false
      );

      // Add AI response
      const aiMessage: ChatMessage = {
        id: response.id,
        sender: 'ai',
        content: response.content,
        created_at: response.created_at,
      };

      set((state) => ({
        messages: [...state.messages, aiMessage],
        loading: false,
        currentMessage: '',
      }));
    } catch (error: any) {
      set({
        loading: false,
        error: error.message || 'Failed to send message',
      });
      // Remove user message on error
      set((state) => ({
        messages: state.messages.filter((m) => m.id !== userMessage.id),
      }));
      throw error;
    }
  },

  // Fetch Chat History
  fetchHistory: async (skip = 0, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const history = await chatService.getChatHistory(skip, limit);
      set({
        messages: history.map((msg) => ({
          ...msg,
          sender: msg.sender as 'user' | 'ai',
        })),
        loading: false,
      });
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to fetch history' });
    }
  },

  // Delete Message
  deleteMessage: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await chatService.deleteChat(id);
      set((state) => ({
        messages: state.messages.filter((msg) => msg.id !== id),
        loading: false,
      }));
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Failed to delete message' });
      throw error;
    }
  },

  // Clear Chat
  clearChat: () => {
    set({
      messages: [],
      currentMessage: '',
      error: null,
    });
  },

  // Set Current Message
  setCurrentMessage: (message: string) => {
    set({ currentMessage: message });
  },

  // Set Model
  setModel: (model: string) => {
    set({ selectedModel: model });
  },

  // Set Documents
  setDocuments: (documentIds: string[]) => {
    set({ selectedDocuments: documentIds });
  },

  // Set Search Mode
  setSearchMode: (mode: 'semantic' | 'hybrid' | 'keyword') => {
    set({ searchMode: mode });
  },

  // Auto Select Model
  autoSelectModel: async (query: string) => {
    try {
      const result = await chatService.selectBestModel(query);
      set({ selectedModel: result.selected_model });
    } catch (error: any) {
      console.error('Failed to auto-select model:', error);
    }
  },

  // Summarize Documents
  summarizeDocuments: async (documentIds: string[], type = 'short') => {
    set({ loading: true, error: null });
    try {
      const result = await chatService.summarizeDocuments({
        document_ids: documentIds,
        summary_type: type as any,
        model_name: get().selectedModel,
      });
      set({ loading: false });
      return result.summary;
    } catch (error: any) {
      set({ loading: false, error: error.message || 'Summarization failed' });
      throw error;
    }
  },

  // Clear Error
  clearError: () => {
    set({ error: null });
  },
}));