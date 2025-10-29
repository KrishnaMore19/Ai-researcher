// services/chatService.ts
import api from './api';
import { config } from '@/lib/config';

interface ChatRequest {
  message: string;
  document_ids?: string[];
  model_name?: string;
}

interface ChatResponse {
  id: string;
  session_id?: string;
  sender: string;
  content: string;
  created_at: string;
}

interface SummarizeRequest {
  document_ids: string[];
  summary_type?: 'short' | 'detailed' | 'bullet' | 'section';
  model_name?: string;
}

interface SummarizeResponse {
  success: boolean;
  summary: string;
  summary_type: string;
  document_count: number;
}

interface ModelSelectionResponse {
  success: boolean;
  selected_model: string;
  model_name: string;
  strengths: string[];
  reason: string;
}

class ChatService {
  /**
   * Validate model
   */
  private validateModel(modelName: string): void {
    if (!config.availableModels.includes(modelName)) {
      throw new Error(`Model ${modelName} is not available. Available models: ${config.availableModels.join(', ')}`);
    }
  }

  /**
   * Send a message to AI
   */
  async sendMessage(
    message: string,
    documentIds?: string[],
    modelName: string = config.defaultModel,
    searchMode: string = 'semantic',
    autoSelectModel: boolean = false
  ): Promise<ChatResponse> {
    // Check if chat feature is enabled
    if (!config.features.chat) {
      throw new Error('Chat feature is disabled');
    }

    // Validate model
    this.validateModel(modelName);

    const chatRequest: ChatRequest = {
      message,
      document_ids: documentIds,
      model_name: modelName,
    };

    const response = await api.post<ChatResponse>('/chat/', chatRequest, {
      params: {
        search_mode: searchMode,
        auto_select_model: autoSelectModel,
      },
    });

    return response.data;
  }

  /**
   * Get chat history
   */
  async getChatHistory(skip: number = 0, limit: number = config.pagination.chatsPerPage): Promise<ChatResponse[]> {
    if (!config.features.chat) {
      throw new Error('Chat feature is disabled');
    }

    const response = await api.get<ChatResponse[]>('/chat/', {
      params: { skip, limit },
    });
    return response.data;
  }

  /**
   * Get a single chat message by ID
   */
  async getChatMessage(chatId: string): Promise<ChatResponse> {
    if (!config.features.chat) {
      throw new Error('Chat feature is disabled');
    }

    const response = await api.get<ChatResponse>(`/chat/${chatId}`);
    return response.data;
  }

  /**
   * Delete a chat message
   */
  async deleteChat(chatId: string): Promise<{ detail: string }> {
    if (!config.features.chat) {
      throw new Error('Chat feature is disabled');
    }

    const response = await api.delete<{ detail: string }>(`/chat/${chatId}`);
    return response.data;
  }

  /**
   * Generate document summary
   */
  async summarizeDocuments(request: SummarizeRequest): Promise<SummarizeResponse> {
    if (!config.features.chat) {
      throw new Error('Chat feature is disabled');
    }

    // Validate model if provided
    if (request.model_name) {
      this.validateModel(request.model_name);
    }

    const response = await api.post<SummarizeResponse>('/chat/summarize', request);
    return response.data;
  }

  /**
   * Auto-select best AI model for query
   */
  async selectBestModel(
    query: string,
    documentContent?: string
  ): Promise<ModelSelectionResponse> {
    if (!config.features.chat) {
      throw new Error('Chat feature is disabled');
    }

    const response = await api.post<ModelSelectionResponse>('/chat/select-model', null, {
      params: {
        query,
        document_content: documentContent,
      },
    });
    return response.data;
  }

  /**
   * Get available models
   */
  getAvailableModels(): string[] {
    return config.availableModels;
  }

  /**
   * Get default model
   */
  getDefaultModel(): string {
    return config.defaultModel;
  }
}

export default new ChatService();