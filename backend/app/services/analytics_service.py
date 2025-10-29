# app/services/analytics_service.py
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, date
import logging

from app.models.analytics import Analytics
from app.models.document import Document
from app.schemas.analytics import (
    AnalyticsResponse, 
    AnalyticsSummaryResponse
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service to manage user analytics:
    - Track document uploads and views
    - Log AI queries and responses
    - Calculate productivity metrics
    - Generate analytics summaries
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------
    # Get document name from database
    # ------------------------------
    async def _get_document_name(self, document_id: str) -> str:
        """
        Fetch document name from database by document_id
        """
        try:
            doc_uuid = UUID(document_id) if isinstance(document_id, str) else document_id
            query = await self.db.execute(
                select(Document).where(Document.id == doc_uuid)
            )
            document = query.scalar_one_or_none()
            
            if document and document.name:
                return document.name
            
            logger.warning(f"Document not found or has no name: {document_id}")
            return "Deleted Document"
        except Exception as e:
            logger.error(f"Error fetching document name for {document_id}: {e}")
            return "Deleted Document"

    # ------------------------------
    # Create or get user analytics entry
    # ------------------------------
    async def get_or_create_analytics(
        self,
        user_id: str
    ) -> Analytics:
        """
        Get existing analytics for user or create new one
        """
        # Convert to UUID if string
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        query = await self.db.execute(
            select(Analytics).where(Analytics.user_id == user_uuid)
        )
        analytics = query.scalar_one_or_none()
        
        if not analytics:
            analytics = Analytics(user_id=user_uuid)
            self.db.add(analytics)
            await self.db.commit()
            await self.db.refresh(analytics)
            logger.info(f"Created new analytics entry for user {user_id}")
        
        return analytics

    # ------------------------------
    # Log document upload event
    # ------------------------------
    async def log_document_upload(
        self,
        user_id: str,
        document_id: str,
        document_name: str = None
    ) -> AnalyticsResponse:
        """
        Track when a user uploads a document
        """
        analytics = await self.get_or_create_analytics(user_id)
        
        # ALWAYS get document name from DB to ensure accuracy
        actual_document_name = await self._get_document_name(document_id)
        
        # Increment total documents
        analytics.total_documents = (analytics.total_documents or 0) + 1
        
        # Add to upload history
        if not analytics.document_uploads:
            analytics.document_uploads = []
        
        analytics.document_uploads.append({
            "document_id": str(document_id),
            "document_name": actual_document_name,
            "timestamp": datetime.now().isoformat()
        })
        
        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)
        
        logger.info(f"Logged document upload: {actual_document_name}")
        
        return AnalyticsResponse.from_orm(analytics)

    # ------------------------------
    # Log document view/access event
    # ------------------------------
    async def log_document_view(
        self,
        user_id: str,
        document_id: str,
        document_name: str = None
    ) -> AnalyticsResponse:
        """
        Track when a user views/accesses a document
        """
        analytics = await self.get_or_create_analytics(user_id)
        
        # ALWAYS get document name from DB to ensure accuracy
        actual_document_name = await self._get_document_name(document_id)
        
        if not analytics.document_views:
            analytics.document_views = []
        
        analytics.document_views.append({
            "document_id": str(document_id),
            "document_name": actual_document_name,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update top documents with proper names
        analytics.top_documents = self._calculate_top_documents(
            analytics.document_views
        )
        
        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)
        
        logger.info(f"Logged document view: {actual_document_name}")
        
        return AnalyticsResponse.from_orm(analytics)

    # ------------------------------
    # Log AI query event
    # ------------------------------
    async def log_ai_query(
        self,
        user_id: str,
        model_name: str,
        query_text: str,
        response_text: str,
        success: bool = True,
        tokens_used: Optional[int] = None
    ) -> AnalyticsResponse:
        """
        Track AI queries and responses
        """
        analytics = await self.get_or_create_analytics(user_id)
        
        # Increment query counters
        analytics.total_queries = (analytics.total_queries or 0) + 1
        if success:
            analytics.successful_queries = (analytics.successful_queries or 0) + 1
        
        # Add to query history
        if not analytics.query_history:
            analytics.query_history = []
        
        analytics.query_history.append({
            "model": model_name,
            "query": query_text[:200],  # Truncate for storage
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "tokens": tokens_used or 0
        })
        
        # Keep only last 100 queries
        if len(analytics.query_history) > 100:
            analytics.query_history = analytics.query_history[-100:]
        
        # Update productivity score
        analytics.productivity_score = self._calculate_productivity_score(
            analytics.total_documents,
            analytics.total_queries,
            analytics.successful_queries
        )
        
        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)
        
        logger.info(f"Logged AI query with model: {model_name}")
        
        return AnalyticsResponse.from_orm(analytics)

    # ------------------------------
    # Get user analytics
    # ------------------------------
    async def get_user_analytics(
        self,
        user_id: str
    ) -> Optional[AnalyticsResponse]:
        """
        Get full analytics for a user and fix any unknown document names
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        query = await self.db.execute(
            select(Analytics).where(Analytics.user_id == user_uuid)
        )
        analytics = query.scalar_one_or_none()
        
        if not analytics:
            return None
        
        # Fix any "Unknown" or missing names in existing data
        await self._fix_unknown_document_names(analytics)
        
        return AnalyticsResponse.from_orm(analytics)

    # ------------------------------
    # Fix unknown document names in existing analytics
    # ------------------------------
    async def _fix_unknown_document_names(self, analytics: Analytics):
        """
        Go through analytics and replace 'Unknown' with actual document names from DB
        """
        updated = False
        
        # Fix document uploads
        if analytics.document_uploads:
            for upload in analytics.document_uploads:
                current_name = upload.get("document_name", "")
                if current_name in ["Unknown", "Unknown Document", "", None]:
                    doc_id = upload.get("document_id")
                    if doc_id:
                        real_name = await self._get_document_name(doc_id)
                        upload["document_name"] = real_name
                        updated = True
                        logger.info(f"Fixed upload: {doc_id} -> {real_name}")
        
        # Fix document views
        if analytics.document_views:
            for view in analytics.document_views:
                current_name = view.get("document_name", "")
                if current_name in ["Unknown", "Unknown Document", "", None]:
                    doc_id = view.get("document_id")
                    if doc_id:
                        real_name = await self._get_document_name(doc_id)
                        view["document_name"] = real_name
                        updated = True
                        logger.info(f"Fixed view: {doc_id} -> {real_name}")
        
        # Recalculate top documents with fixed names
        if updated:
            if analytics.document_views:
                analytics.top_documents = self._calculate_top_documents(
                    analytics.document_views
                )
            
            self.db.add(analytics)
            await self.db.commit()
            await self.db.refresh(analytics)
            logger.info(f"Updated analytics with {updated} fixed document names")

    # ------------------------------
    # Get analytics summary
    # ------------------------------
    async def get_summary(
        self,
        user_id: str
    ) -> AnalyticsSummaryResponse:
        """
        Get analytics summary for dashboard
        """
        analytics = await self.get_user_analytics(user_id)
        
        if not analytics:
            return AnalyticsSummaryResponse()
        
        query_success_rate = 0.0
        if analytics.total_queries and analytics.total_queries > 0:
            query_success_rate = (
                analytics.successful_queries / analytics.total_queries * 100
            )
        
        return AnalyticsSummaryResponse(
            total_documents=analytics.total_documents or 0,
            total_queries=analytics.total_queries or 0,
            successful_queries=analytics.successful_queries or 0,
            query_success_rate=round(query_success_rate, 2),
            productivity_score=analytics.productivity_score or 0.0
        )

    # ------------------------------
    # Helper methods
    # ------------------------------
    
    def _calculate_top_documents(self, document_views: List[dict]) -> List[dict]:
        """
        Calculate most viewed documents from view history
        Filter out "Unknown" and "Deleted Document"
        """
        if not document_views:
            return []
        
        # Count views by document, excluding unknown/deleted
        view_counts = {}
        excluded_names = ["Unknown", "Unknown Document", "Deleted Document", "", None]
        
        for view in document_views:
            doc_name = view.get("document_name", "")
            
            # Skip excluded documents
            if doc_name in excluded_names:
                continue
                
            view_counts[doc_name] = view_counts.get(doc_name, 0) + 1
        
        if not view_counts:
            return []
        
        # Sort by count
        sorted_docs = sorted(
            view_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        total_views = sum(view_counts.values())
        
        return [
            {
                "name": name,
                "views": count,
                "percentage": int((count / total_views) * 100) if total_views > 0 else 0
            }
            for name, count in sorted_docs
        ]

    def _calculate_productivity_score(
        self,
        total_documents: int,
        total_queries: int,
        successful_queries: int
    ) -> float:
        """
        Calculate productivity score (0-100)
        Based on documents uploaded and successful queries
        """
        if not total_documents and not total_queries:
            return 0.0
        
        # Weighted calculation
        doc_score = min(total_documents * 5, 50)  # Max 50 points for docs
        
        if total_queries > 0:
            query_score = min(
                (successful_queries / total_queries) * total_queries,
                50
            )
        else:
            query_score = 0
        
        total_score = doc_score + query_score
        return min(round(total_score, 2), 100.0)