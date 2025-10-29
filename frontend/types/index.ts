// types/index.ts
// Export all types from a single entry point

// Auth types
export type {
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  TokenData,
  AuthState,
} from './auth';

// Document types
export type {
  Document,
  DocumentCreate,
  DocumentUpdate,
  SearchRequest,
  SearchResult,
  SearchChunk,
  Citation,
  CitationResponse,
  BibliographyResponse,
  ComparisonResponse,
  ComparisonData,
  DocumentFilters,
  EmbeddingResponse,
} from './document';

// Chat types
export type {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  ChatSession,
  SummarizeRequest,
  SummarizeResponse,
  ModelSelectionResponse,
  ModelInfo,
  SearchMode,
  ChatState,
} from './chat';

// Note types
export type {
  Note,
  NoteCreate,
  NoteUpdate,
  NoteFilters,
  NotesState,
} from './note';

// Analytics types
export type {
  DocumentUploadEvent,
  DocumentViewEvent,
  QueryHistoryEvent,
  TopDocument,
  DocumentMetric,
  QueryHistoryItem,
  QueryInsightItem,
  TimeSavedItem,
  ActivityHour,
  ActivityDay,
  Analytics,
  AnalyticsSummary,
  AnalyticsEventCreate,
  DateRange,
  AnalyticsState,
} from './analytics';

// Subscription types
export type {
  BillingHistory,
  Subscription,
  SubscriptionCreate,
  SubscriptionUpdate,
  SubscriptionUpgradeRequest,
  PaymentOrderResponse,
  PaymentVerificationRequest,
  PaymentVerificationResponse,
  PaymentModalState,
  Plan,
  PlanName,
  UsageStats,
  SettingsState,
} from './subscription';

// Common/Shared types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface PaginationMeta {
  total: number;
  skip: number;
  limit: number;
  hasMore: boolean;
}

export interface ErrorResponse {
  detail: string;
  status?: number;
}

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

export interface Modal {
  [key: string]: boolean;
}

export interface UIState {
  sidebarOpen: boolean;
  modals: Modal;
  toasts: Toast[];
  globalLoading: boolean;
  theme: 'light' | 'dark';
}