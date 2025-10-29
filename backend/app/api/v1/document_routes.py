# app/api/v1/document_routes.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import os

from app.schemas import document as document_schema
from app.services.document_service import DocumentService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.citation_service import CitationService
from app.db.session import get_db
from app.utils.file_handler import save_upload_file

router = APIRouter(prefix="/documents", tags=["documents"])

# Request schemas
class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., example="machine learning algorithms")
    document_ids: Optional[List[str]] = None
    search_mode: str = Field("semantic", example="semantic")
    top_k: int = Field(5, ge=1, le=20)
    expand_query: bool = True

class ExtractCitationsRequest(BaseModel):
    format_hint: Optional[str] = Field(None, example="apa")

# Helper function to log analytics (DRY principle)
async def log_analytics_safe(db: AsyncSession, log_func, **kwargs):
    """Safely log analytics without breaking main flow"""
    try:
        analytics_service = AnalyticsService(db)
        await log_func(analytics_service, **kwargs)
    except Exception as e:
        print(f"Analytics logging error: {e}")

# ------------------------------
# CRUD Operations
# ------------------------------
@router.post(
    "/", 
    response_model=document_schema.DocumentResponse,
    summary="Upload a new document",
    description="Upload a document file with a title"
)
async def upload_document(
    title: str = Form(..., description="Title/name for the document"),
    file: UploadFile = File(..., description="The document file to upload"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """Upload a new document and log to analytics"""
    file_path = save_upload_file(file)
    
    file_type = file.filename.split(".")[-1].upper() if file.filename else "UNKNOWN"
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    
    document_service = DocumentService(db)
    doc = await document_service.create_document(
        user_id=str(current_user.id),
        title=title,
        file_path=file_path,
        file_type=file_type,
        file_size=f"{file_size_mb} MB"
    )
    
    await log_analytics_safe(
        db, 
        lambda svc, **kw: svc.log_document_upload(**kw),
        user_id=str(current_user.id),
        document_id=str(doc.id),
        document_name=title
    )
    
    return doc

@router.get(
    "/", 
    response_model=List[document_schema.DocumentResponse],
    summary="Get all documents",
    description="Retrieve all documents for the current user with pagination"
)
async def get_user_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """Get all documents for the current user"""
    document_service = DocumentService(db)
    return await document_service.get_documents(
        user_id=str(current_user.id), 
        skip=skip, 
        limit=limit
    )

@router.get(
    "/{document_id}", 
    response_model=document_schema.DocumentResponse,
    summary="Get a specific document",
    description="Retrieve a single document by its UUID"
)
async def get_document(
    document_id: UUID = Path(..., description="The UUID of the document to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """Get a single document and log view to analytics"""
    document_service = DocumentService(db)
    doc = await document_service.get_document(
        document_id=str(document_id), 
        user_id=str(current_user.id)
    )
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document not found"
        )
    
    await log_analytics_safe(
        db,
        lambda svc, **kw: svc.log_document_view(**kw),
        user_id=str(current_user.id),
        document_id=str(document_id),
        document_name=doc.name
    )
    
    return doc

@router.delete(
    "/{document_id}",
    response_model=dict,
    summary="Delete a document",
    description="Soft delete a document by its UUID"
)
async def delete_document(
    document_id: UUID = Path(..., description="The UUID of the document to delete"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """Delete a document"""
    document_service = DocumentService(db)
    success = await document_service.delete_document(
        document_id=str(document_id), 
        user_id=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or cannot be deleted"
        )
    
    return {"detail": "Document deleted successfully"}

# ------------------------------
# Advanced Search
# ------------------------------
@router.post("/search", summary="Advanced semantic search")
async def advanced_search(
    request: AdvancedSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Perform advanced semantic search across documents.
    
    **Search Modes:**
    - `semantic`: Vector-based similarity (best for concepts)
    - `keyword`: Exact keyword matching
    - `hybrid`: Combination of both (recommended)
    
    **Query Expansion:** Automatically expands "ML" to "ML machine learning"
    """
    doc_service = DocumentService(db)
    
    try:
        results = await doc_service.search_similar_chunks_advanced(
            query=request.query,
            doc_ids=request.document_ids,
            search_mode=request.search_mode,
            top_k=request.top_k,
            expand_query=request.expand_query
        )
        
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

# ------------------------------
# Citation Management
# ------------------------------
@router.post("/{document_id}/citations", summary="Extract citations from document")
async def extract_citations(
    document_id: UUID = Path(...),
    request: ExtractCitationsRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Extract citations from document reference section.
    
    **Supported Formats:** APA, MLA, IEEE
    """
    doc_service = DocumentService(db)
    citation_service = CitationService()
    
    try:
        doc = await doc_service.get_document(str(document_id), str(current_user.id))
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        chunks = await doc_service.search_similar_chunks(
            query="references bibliography citations",
            doc_ids=[str(document_id)],
            top_k=50
        )
        
        document_text = "\n\n".join(chunks)
        citations = citation_service.extract_citations(
            document_text=document_text,
            format_hint=request.format_hint
        )
        
        return {
            "success": True,
            "citations": citations,
            "total_citations": len(citations),
            "document_id": str(document_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation extraction failed: {str(e)}"
        )

@router.get("/{document_id}/bibliography", summary="Generate bibliography")
async def generate_bibliography(
    document_id: UUID = Path(...),
    format_type: str = Query("apa", example="apa"),
    sort_by: str = Query("author", example="author"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Generate formatted bibliography from document citations.
    
    **Parameters:**
    - `format_type`: apa, mla, ieee
    - `sort_by`: author, year, title
    """
    doc_service = DocumentService(db)
    citation_service = CitationService()
    
    try:
        chunks = await doc_service.search_similar_chunks(
            query="references bibliography",
            doc_ids=[str(document_id)],
            top_k=50
        )
        
        document_text = "\n\n".join(chunks)
        citations = citation_service.extract_citations(document_text)
        
        if not citations:
            raise HTTPException(status_code=404, detail="No citations found")
        
        bibliography = citation_service.generate_bibliography(
            citations=citations,
            format_type=format_type,
            sort_by=sort_by
        )
        
        return {
            "success": True,
            "bibliography": bibliography,
            "format": format_type,
            "total_citations": len(citations)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bibliography generation failed: {str(e)}"
        )

# ------------------------------
# Document Comparison
# ------------------------------
@router.post("/compare", summary="Compare multiple documents")
async def compare_documents(
    document_ids: List[str] = Query(..., min_items=2, max_items=10),
    comparison_aspects: Optional[List[str]] = Query(None),
    include_contradictions: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Compare multiple research documents.
    
    **Example:** `/documents/compare?document_ids=uuid1&document_ids=uuid2&document_ids=uuid3`
    """
    from app.services.comparison_service import ComparisonService
    from app.services.llm_service import llm_service
    
    comparison_service = ComparisonService(db, llm_service)
    
    try:
        result = await comparison_service.compare_documents(
            document_ids=document_ids,
            comparison_aspects=comparison_aspects,
            include_contradictions=include_contradictions
        )
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )