# app/api/v1/chat_routes.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.schemas import chat as chat_schema
from app.services.chat_service import ChatService
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import llm_service
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.db.session import get_db

router = APIRouter(prefix="/chat", tags=["chat"])

# Request schemas
class SummarizeRequest(BaseModel):
    document_ids: List[str] = Field(..., min_items=1)
    summary_type: str = Field("short", example="short")
    model_name: Optional[str] = Field("llama", example="llama")

# Helper function for analytics (DRY principle)
async def log_analytics_safe(db: AsyncSession, log_func, **kwargs):
    """Safely log analytics without breaking main flow"""
    try:
        analytics_service = AnalyticsService(db)
        await log_func(analytics_service, **kwargs)
    except Exception as e:
        print(f"Analytics logging error: {e}")

# ------------------------------
# Core Chat Operations
# ------------------------------
@router.post("/", response_model=chat_schema.ChatResponse)
async def send_message(
    chat_request: chat_schema.ChatRequest,
    search_mode: str = Query("semantic", example="semantic"),
    auto_select_model: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Send a message to the AI and get a response.
    
    **Parameters:**
    - `search_mode`: semantic, hybrid, or keyword
    - `auto_select_model`: Auto-select best model for query
    """
    chat_service = ChatService(db, llm_service)
    
    response = await chat_service.send_message(
        user_id=str(current_user.id),
        message=chat_request.message,
        document_ids=[str(doc_id) for doc_id in (chat_request.document_ids or [])],
        model_name=chat_request.model_name,
        search_mode=search_mode,
        auto_select_model=auto_select_model
    )
    
    await log_analytics_safe(
        db,
        lambda svc, **kw: svc.log_ai_query(**kw),
        user_id=str(current_user.id),
        model_name=chat_request.model_name,
        query_text=chat_request.message,
        response_text=response.content,
        success=True,
        tokens_used=None
    )
    
    return response

@router.get("/", response_model=List[chat_schema.ChatResponse])
async def get_chat_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """Get chat history for the current user"""
    chat_service = ChatService(db, llm_service)
    return await chat_service.get_user_chat_history(
        user_id=str(current_user.id),
        skip=skip,
        limit=limit
    )

@router.get("/{chat_id}", response_model=chat_schema.ChatResponse)
async def get_chat_message(
    chat_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """Get a single chat message by its UUID"""
    chat_service = ChatService(db, llm_service)
    history = await chat_service.get_user_chat_history(
        user_id=str(current_user.id),
        skip=0,
        limit=1000
    )
    
    message = next((m for m in history if str(m.id) == str(chat_id)), None)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat message not found"
        )
    return message

@router.delete("/{chat_id}", response_model=dict)
async def delete_chat(
    chat_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """Delete a chat message by its UUID"""
    chat_service = ChatService(db, llm_service)
    success = await chat_service.delete_chat(
        chat_id=str(chat_id), 
        user_id=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chat message not found or cannot be deleted"
        )
    
    return {"detail": "Chat message deleted successfully"}

# ------------------------------
# Advanced Summarization
# ------------------------------
@router.post("/summarize", summary="Generate document summary")
async def summarize_documents(
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Generate advanced summaries with multiple styles.
    
    **Summary Types:**
    - `short`: 3-5 sentence concise summary
    - `detailed`: Comprehensive with methodology, findings, conclusions
    - `bullet`: Key points as bullet list
    - `section`: Section-wise breakdown
    """
    doc_service = DocumentService(db)
    
    try:
        all_chunks = []
        for doc_id in request.document_ids:
            chunks = await doc_service.search_similar_chunks(
                query="summary overview key points",
                doc_ids=[doc_id],
                top_k=15
            )
            all_chunks.extend(chunks)
        
        content = "\n\n".join(all_chunks)
        
        summary = await llm_service.generate_summary(
            content=content,
            summary_type=request.summary_type,
            model_name=request.model_name
        )
        
        return {
            "success": True,
            "summary": summary,
            "summary_type": request.summary_type,
            "document_count": len(request.document_ids)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )

# ------------------------------
# Model Selection
# ------------------------------
@router.post("/select-model", summary="Auto-select best AI model")
async def select_best_model(
    query: str = Query(..., example="Explain the methodology"),
    document_content: Optional[str] = Query(None),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Automatically select the best AI model for a query.
    
    **Model Strengths:**
    - **Llama**: Factual queries, specialized domains
    - **Dolphin**: Creative tasks, conversational
    - **Gemma**: Analytical, comparisons, summaries
    """
    try:
        selected_model = await llm_service.select_best_model(
            query=query,
            document_content=document_content or ""
        )
        
        model_info = llm_service.get_model(selected_model)
        
        return {
            "success": True,
            "selected_model": selected_model,
            "model_name": model_info["name"],
            "strengths": model_info.get("strengths", []),
            "reason": "Selected based on query type and content analysis"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model selection failed: {str(e)}"
        )