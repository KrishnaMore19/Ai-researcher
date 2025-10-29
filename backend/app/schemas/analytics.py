from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date

# Simple event tracking structures
class DocumentUploadEvent(BaseModel):
    document_id: str
    document_name: str
    timestamp: str

class DocumentViewEvent(BaseModel):
    document_id: str
    document_name: str
    timestamp: str

class QueryHistoryEvent(BaseModel):
    model: str
    query: str
    timestamp: str
    success: bool
    tokens: Optional[int] = 0

# Aggregated metric structures (for display)
class DocumentMetric(BaseModel):
    month: str
    count: int
    views: Optional[int] = 0

class TopDocument(BaseModel):
    name: str
    views: int
    percentage: int

class QueryHistoryItem(BaseModel):
    week: str
    queries: int
    successful: int

class QueryInsightItem(BaseModel):
    type: str
    count: int

class TimeSavedItem(BaseModel):
    month: str
    timeSaved: float
    manualTime: float

class ActivityHour(BaseModel):
    hour: int
    activity: int

class ActivityDay(BaseModel):
    day: str
    hours: List[ActivityHour]

# Main Analytics schemas
class AnalyticsBase(BaseModel):
    total_documents: Optional[int] = 0
    total_queries: Optional[int] = 0
    successful_queries: Optional[int] = 0
    productivity_score: Optional[float] = 0.0

class AnalyticsCreate(BaseModel):
    document_id: Optional[UUID] = None
    event_type: str = Field(..., example="document_view")
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsRead(AnalyticsBase):
    id: UUID
    user_id: UUID
    
    # Raw event data
    document_uploads: Optional[List[DocumentUploadEvent]] = []
    document_views: Optional[List[DocumentViewEvent]] = []
    query_history: Optional[List[QueryHistoryEvent]] = []
    
    # Top documents summary
    top_documents: Optional[List[TopDocument]] = []
    
    created_at: date
    updated_at: date

    class Config:
        from_attributes = True

class AnalyticsUpdate(AnalyticsBase):
    pass

AnalyticsResponse = AnalyticsRead

class AnalyticsSummaryResponse(BaseModel):
    total_documents: int = 0
    total_queries: int = 0
    successful_queries: int = 0
    query_success_rate: float = 0.0
    productivity_score: float = 0.0

# Deprecated schemas (kept for reference)
class DocumentEmbeddingResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    embedding: List[float]

    class Config:
        from_attributes = True

class AIQueryLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    model_name: str
    query: str
    response: str
    tokens_used: Optional[int] = None

    class Config:
        from_attributes = True