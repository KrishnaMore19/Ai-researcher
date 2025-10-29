// types/analytics.ts

export interface DocumentUploadEvent {
  document_id: string;
  document_name: string;
  timestamp: string;
}

export interface DocumentViewEvent {
  document_id: string;
  document_name: string;
  timestamp: string;
}

export interface QueryHistoryEvent {
  model: string;
  query: string;
  timestamp: string;
  success: boolean;
  tokens?: number;
}

export interface TopDocument {
  name: string;
  views: number;
  percentage: number;
}

export interface DocumentMetric {
  month: string;
  count: number;
  views?: number;
}

export interface QueryHistoryItem {
  week: string;
  queries: number;
  successful: number;
}

export interface QueryInsightItem {
  type: string;
  count: number;
}

export interface TimeSavedItem {
  month: string;
  timeSaved: number;
  manualTime: number;
}

export interface ActivityHour {
  hour: number;
  activity: number;
}

export interface ActivityDay {
  day: string;
  hours: ActivityHour[];
}

export interface Analytics {
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

export interface AnalyticsSummary {
  total_documents: number;
  total_queries: number;
  successful_queries: number;
  query_success_rate: number;
  productivity_score: number;
}

export interface AnalyticsEventCreate {
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

export interface DateRange {
  start: string | null;
  end: string | null;
}

export interface AnalyticsState {
  analytics: Analytics | null;
  summary: AnalyticsSummary | null;
  loading: boolean;
  error: string | null;
  dateRange: DateRange;
}