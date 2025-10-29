// services/documentService.ts
import api, { uploadFile } from './api';
import { config } from '@/lib/config';

interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  status: string;
  uploaded_date: string;
  is_active: boolean;
}

interface SearchRequest {
  query: string;
  document_ids?: string[];
  search_mode?: 'semantic' | 'keyword' | 'hybrid';
  top_k?: number;
  expand_query?: boolean;
}

interface SearchResult {
  success: boolean;
  data: any[];
}

interface CitationResponse {
  success: boolean;
  citations: any[];
  total_citations: number;
  document_id: string;
}

interface BibliographyResponse {
  success: boolean;
  bibliography: string;
  format: string;
  total_citations: number;
}

interface ComparisonResponse {
  success: boolean;
  data: any;
}

class DocumentService {
  /**
   * Validate file before upload
   */
  private validateFile(file: File): void {
    // Check file size
    if (file.size > config.maxFileSize) {
      throw new Error(`File size exceeds limit of ${config.maxFileSize / (1024 * 1024)}MB`);
    }

    // Check file type
    const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
    if (!config.allowedFileTypes.includes(fileExtension)) {
      throw new Error(`File type ${fileExtension} is not allowed. Allowed types: ${config.allowedFileTypes.join(', ')}`);
    }
  }

  /**
   * Upload a new document
   */
  async uploadDocument(file: File, title: string): Promise<Document> {
    // Validate file
    this.validateFile(file);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    const response = await uploadFile('/documents/', formData);
    return response.data;
  }

  /**
   * Get all documents with pagination
   */
  async getDocuments(skip: number = 0, limit: number = config.pagination.documentsPerPage): Promise<Document[]> {
    const response = await api.get<Document[]>('/documents/', {
      params: { skip, limit },
    });
    return response.data;
  }

  /**
   * Get a single document by ID
   */
  async getDocument(documentId: string): Promise<Document> {
    const response = await api.get<Document>(`/documents/${documentId}`);
    return response.data;
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<{ detail: string }> {
    const response = await api.delete<{ detail: string }>(`/documents/${documentId}`);
    return response.data;
  }

  /**
   * Advanced semantic search across documents
   */
  async searchDocuments(searchRequest: SearchRequest): Promise<SearchResult> {
    const response = await api.post<SearchResult>('/documents/search', searchRequest);
    return response.data;
  }

  /**
   * Extract citations from a document
   */
  async extractCitations(
    documentId: string,
    formatHint?: string
  ): Promise<CitationResponse> {
    // Check if feature is enabled
    if (!config.features.citations) {
      throw new Error('Citation extraction feature is disabled');
    }

    const response = await api.post<CitationResponse>(
      `/documents/${documentId}/citations`,
      { format_hint: formatHint }
    );
    return response.data;
  }

  /**
   * Generate formatted bibliography
   */
  async generateBibliography(
    documentId: string,
    formatType: string = 'apa',
    sortBy: string = 'author'
  ): Promise<BibliographyResponse> {
    // Check if feature is enabled
    if (!config.features.citations) {
      throw new Error('Bibliography generation feature is disabled');
    }

    const response = await api.get<BibliographyResponse>(
      `/documents/${documentId}/bibliography`,
      {
        params: { format_type: formatType, sort_by: sortBy },
      }
    );
    return response.data;
  }

  /**
   * Compare multiple documents
   */
  async compareDocuments(
    documentIds: string[],
    comparisonAspects?: string[],
    includeContradictions: boolean = true
  ): Promise<ComparisonResponse> {
    // Check if feature is enabled
    if (!config.features.documentComparison) {
      throw new Error('Document comparison feature is disabled');
    }

    const params = new URLSearchParams();
    documentIds.forEach((id) => params.append('document_ids', id));
    
    if (comparisonAspects) {
      comparisonAspects.forEach((aspect) => params.append('comparison_aspects', aspect));
    }
    
    params.append('include_contradictions', includeContradictions.toString());

    const response = await api.post<ComparisonResponse>(
      `/documents/compare?${params.toString()}`
    );
    return response.data;
  }
}

export default new DocumentService();