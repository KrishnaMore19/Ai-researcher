// types/document.ts

export interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  status: string;
  uploaded_date: string;
  is_active: boolean;
}

export interface DocumentCreate {
  name: string;
  type: string;
  size: string;
  status?: string;
}

export interface DocumentUpdate {
  name?: string;
  type?: string;
  size?: string;
  status?: string;
  is_active?: boolean;
}

export interface SearchRequest {
  query: string;
  document_ids?: string[];
  search_mode?: 'semantic' | 'keyword' | 'hybrid';
  top_k?: number;
  expand_query?: boolean;
}

export interface SearchResult {
  success: boolean;
  data: SearchChunk[];
}

export interface SearchChunk {
  document_id: string;
  chunk_content: string;
  similarity_score?: number;
}

export interface Citation {
  authors: string[];
  title: string;
  year: number;
  source?: string;
  doi?: string;
  url?: string;
}

export interface CitationResponse {
  success: boolean;
  citations: Citation[];
  total_citations: number;
  document_id: string;
}

export interface BibliographyResponse {
  success: boolean;
  bibliography: string;
  format: string;
  total_citations: number;
}

export interface ComparisonResponse {
  success: boolean;
  data: ComparisonData;
}

export interface ComparisonData {
  similarities: string[];
  differences: string[];
  contradictions?: string[];
  summary: string;
}

export interface DocumentFilters {
  type: string | null;
  status: string | null;
  searchQuery: string;
}

export interface EmbeddingResponse {
  document_id: string;
  chunk_content: string;
  embedding_vector: number[];
}