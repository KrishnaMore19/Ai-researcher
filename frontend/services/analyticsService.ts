// services/analyticsService.ts
import api from './api';
import { config } from '@/lib/config';

interface DocumentUploadEvent {
  document_id: string;
  document_name: string;
  timestamp: string;
}

interface DocumentViewEvent {
  document_id: string;
  document_name: string;
  timestamp: string;
}

interface QueryHistoryEvent {
  model: string;
  query: string;
  timestamp: string;
  success: boolean;
  tokens?: number;
}

interface TopDocument {
  name: string;
  views: number;
  percentage: number;
}

interface Analytics {
  id: string;
  user_id: string;
  total_documents: number;
  total_queries: number;
  successful_queries: number;
  productivity_score: number;
  document_uploads: DocumentUploadEvent[];
  document_views: DocumentViewEvent[];
  query_history: QueryHistoryEvent[];
  top_documents: TopDocument[];
  created_at: string;
  updated_at: string;
}

interface AnalyticsSummary {
  total_documents: number;
  total_queries: number;
  successful_queries: number;
  query_success_rate: number;
  productivity_score: number;
}

interface AnalyticsEventCreate {
  event_type: 'document_upload' | 'document_view' | 'ai_query';
  document_id?: string;
  metadata?: {
    document_name?: string;
    model_name?: string;
    query_text?: string;
    response_text?: string;
    success?: boolean;
    tokens_used?: number;
  };
}

class AnalyticsService {
  /**
   * Check if analytics feature is enabled
   */
  private checkFeatureEnabled(): void {
    if (!config.features.analytics) {
      throw new Error('Analytics feature is disabled');
    }
  }

  /**
   * Check if analytics logging is enabled
   */
  private isLoggingEnabled(): boolean {
    return config.enableAnalyticsLogging;
  }

  /**
   * Get complete analytics for user
   */
  async getAnalytics(skip: number = 0, limit: number = 50): Promise<Analytics> {
    this.checkFeatureEnabled();

    const response = await api.get<Analytics>('/analytics/', {
      params: { skip, limit },
    });
    return response.data;
  }

  /**
   * Get analytics summary for dashboard
   */
  async getSummary(): Promise<AnalyticsSummary> {
    this.checkFeatureEnabled();

    const response = await api.get<AnalyticsSummary>('/analytics/summary');
    return response.data;
  }

  /**
   * Get user analytics
   */
  async getUserAnalytics(): Promise<Analytics> {
    this.checkFeatureEnabled();

    const response = await api.get<Analytics>('/analytics/user');
    return response.data;
  }

  /**
   * Log an analytics event
   */
  async logEvent(event: AnalyticsEventCreate): Promise<Analytics> {
    this.checkFeatureEnabled();

    if (!this.isLoggingEnabled()) {
      if (config.debugMode) {
        console.log('Analytics logging is disabled, skipping event:', event);
      }
      // Return a mock analytics object instead of making API call
      return {} as Analytics;
    }

    const response = await api.post<Analytics>('/analytics/', event);
    return response.data;
  }

  /**
   * Log document upload event
   */
  async logDocumentUpload(documentId: string, documentName: string): Promise<Analytics> {
    return this.logEvent({
      event_type: 'document_upload',
      document_id: documentId,
      metadata: {
        document_name: documentName,
      },
    });
  }

  /**
   * Log document view event
   */
  async logDocumentView(documentId: string, documentName: string): Promise<Analytics> {
    return this.logEvent({
      event_type: 'document_view',
      document_id: documentId,
      metadata: {
        document_name: documentName,
      },
    });
  }

  /**
   * Log AI query event
   */
  async logAIQuery(
    modelName: string,
    queryText: string,
    responseText: string,
    success: boolean = true,
    tokensUsed?: number
  ): Promise<Analytics> {
    return this.logEvent({
      event_type: 'ai_query',
      metadata: {
        model_name: modelName,
        query_text: queryText,
        response_text: responseText,
        success,
        tokens_used: tokensUsed,
      },
    });
  }

  /**
   * Calculate query success rate
   */
  calculateSuccessRate(totalQueries: number, successfulQueries: number): number {
    if (totalQueries === 0) return 0;
    return Math.round((successfulQueries / totalQueries) * 100);
  }

  /**
   * Format productivity score
   */
  formatProductivityScore(score: number): string {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Average';
    if (score >= 20) return 'Low';
    return 'Very Low';
  }

  /**
   * Get productivity color
   */
  getProductivityColor(score: number): string {
    if (score >= 80) return 'green';
    if (score >= 60) return 'blue';
    if (score >= 40) return 'yellow';
    if (score >= 20) return 'orange';
    return 'red';
  }
}

export default new AnalyticsService();