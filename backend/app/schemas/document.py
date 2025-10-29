# app/schemas/document.py
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# Base schema for common properties
class DocumentBase(BaseModel):
    name: str = Field(..., example="ResearchPaper.pdf")
    type: str = Field(..., example="PDF")
    size: str = Field(..., example="2.4 MB")
    status: Optional[str] = Field("processing", example="processing")

# Schema for creating a new document
class DocumentCreate(DocumentBase):
    pass

# Schema for reading/fetching document info
class DocumentRead(DocumentBase):
    id: UUID
    uploaded_date: datetime
    is_active: bool

    class Config:
        from_attributes = True  # Changed from orm_mode in Pydantic v2

# Alias for backward compatibility
DocumentResponse = DocumentRead

# Schema for updating document info
class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    size: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

# Additional schemas for embeddings and RAG
class EmbeddingResponse(BaseModel):
    document_id: UUID
    chunk_content: str
    embedding_vector: List[float]

class SimilarChunkResponse(BaseModel):
    document_id: UUID
    chunk_content: str
    similarity_score: float

    class Config:
        from_attributes = True