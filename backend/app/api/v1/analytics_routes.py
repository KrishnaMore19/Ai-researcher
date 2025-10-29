# app/api/v1/analytics_routes.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import analytics as analytics_schema
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.db.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

# ------------------------------
# GET analytics (with pagination support)
# ------------------------------
@router.get("/", response_model=analytics_schema.AnalyticsResponse)
async def get_analytics(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Get complete analytics for the current user
    """
    analytics_service = AnalyticsService(db)
    analytics = await analytics_service.get_user_analytics(
        user_id=str(current_user.id)
    )
    
    if not analytics:
        # Create and return empty analytics instead of 404
        analytics_obj = await analytics_service.get_or_create_analytics(
            user_id=str(current_user.id)
        )
        return analytics_schema.AnalyticsResponse.from_orm(analytics_obj)
    
    return analytics

# ------------------------------
# Generic analytics event logging
# ------------------------------
@router.post("/", response_model=analytics_schema.AnalyticsResponse, status_code=status.HTTP_201_CREATED)
async def log_analytics_event(
    event: analytics_schema.AnalyticsCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Log analytics event (document upload, view, or query).
    
    Event types:
    - document_upload: When user uploads a document
    - document_view: When user views a document
    - ai_query: When user runs an AI query
    """
    analytics_service = AnalyticsService(db)
    
    event_type = event.event_type.lower()
    metadata = event.metadata or {}
    
    try:
        if event_type == "document_upload":
            result = await analytics_service.log_document_upload(
                user_id=str(current_user.id),
                document_id=str(event.document_id) if event.document_id else "unknown",
                document_name=metadata.get("document_name", "Unknown")
            )
        
        elif event_type == "document_view":
            result = await analytics_service.log_document_view(
                user_id=str(current_user.id),
                document_id=str(event.document_id) if event.document_id else "unknown",
                document_name=metadata.get("document_name", "Unknown")
            )
        
        elif event_type == "ai_query":
            result = await analytics_service.log_ai_query(
                user_id=str(current_user.id),
                model_name=metadata.get("model_name", "unknown"),
                query_text=metadata.get("query_text", ""),
                response_text=metadata.get("response_text", ""),
                success=metadata.get("success", True),
                tokens_used=metadata.get("tokens_used")
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown event type: {event_type}. Valid types: document_upload, document_view, ai_query"
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging event: {str(e)}"
        )

# ------------------------------
# Get user analytics
# ------------------------------
@router.get("/user", response_model=analytics_schema.AnalyticsResponse)
async def get_user_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Get complete analytics for the current user
    """
    analytics_service = AnalyticsService(db)
    analytics = await analytics_service.get_user_analytics(
        user_id=str(current_user.id)
    )
    
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analytics found for user"
        )
    
    return analytics

# ------------------------------
# Get analytics summary (for dashboard)
# ------------------------------
@router.get("/summary", response_model=analytics_schema.AnalyticsSummaryResponse)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Get analytics summary for dashboard
    """
    analytics_service = AnalyticsService(db)
    summary = await analytics_service.get_summary(user_id=str(current_user.id))
    
    return summary