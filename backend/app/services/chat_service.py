# app/services/chat_service.py
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
import logging

from app.models.chat import ChatMessage
from app.models.document import Document
from app.schemas.chat import ChatResponse
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service to manage chat interactions with RAG (Retrieval Augmented Generation).
    
    🆕 NEW FEATURES:
    - Advanced semantic search integration
    - Query classification for better responses
    - Auto model selection
    - Multi-document comparison support
    """

    def __init__(self, db: AsyncSession, llm_service):
        self.db = db
        self.llm_service = llm_service
        self.doc_service = DocumentService(db)

    # ==============================
    # 🆕 ENHANCED MESSAGE HANDLING
    # ==============================

    async def send_message(
        self,
        user_id: str,
        message: str,
        document_ids: List[str] = None,
        model_name: str = "llama",
        search_mode: str = "semantic",  # 🆕 NEW: semantic, hybrid, keyword
        auto_select_model: bool = False,  # 🆕 NEW: auto model selection
        summary_type: Optional[str] = None  # 🆕 NEW: for summarization requests
    ) -> ChatResponse:
        """
        Send a message and get AI response using advanced RAG.
        
        🆕 NEW PARAMETERS:
        - search_mode: Type of search to use (semantic/hybrid/keyword)
        - auto_select_model: Let system choose best model
        - summary_type: If summarizing, specify type (short/detailed/bullet/section)
        
        Flow:
        1. Classify query intent (summarize, compare, question, etc.)
        2. If document_ids provided, perform advanced search
        3. Auto-select model if requested
        4. Generate response with appropriate prompt
        5. Store conversation history
        """
        
        logger.info(f"Processing message: '{message}' with {len(document_ids or [])} documents")
        
        # Step 1: Classify query intent
        query_intent = self._classify_query_intent(message)
        logger.info(f"Query intent: {query_intent}")
        
        # Step 2: Handle different query types
        if query_intent == "comparison" and document_ids and len(document_ids) > 1:
            # Multi-document comparison
            return await self._handle_comparison_query(
                user_id, message, document_ids, model_name
            )
        
        elif query_intent == "summarization" and document_ids:
            # Document summarization
            return await self._handle_summarization_query(
                user_id, message, document_ids, model_name, summary_type
            )
        
        else:
            # Standard RAG query
            return await self._handle_standard_query(
                user_id, message, document_ids, model_name, search_mode, auto_select_model
            )

    async def _handle_standard_query(
        self,
        user_id: str,
        message: str,
        document_ids: List[str],
        model_name: str,
        search_mode: str,
        auto_select_model: bool
    ) -> ChatResponse:
        """
        Handle standard question-answering with RAG.
        """
        # Prepare context from documents using advanced search
        context = ""
        search_metadata = {}
        
        if document_ids and len(document_ids) > 0:
            logger.info(f"Performing {search_mode} search in {len(document_ids)} documents")
            
            # Use advanced search
            search_results = await self.doc_service.search_similar_chunks_advanced(
                query=message,
                doc_ids=document_ids,
                search_mode=search_mode,
                top_k=5,
                expand_query=True  # Enable query expansion
            )
            
            # Extract context from results
            if search_results.get("results"):
                context_chunks = [result["content"] for result in search_results["results"]]
                context = "\n\n---\n\n".join(context_chunks)
                
                search_metadata = {
                    "search_mode": search_results.get("search_mode"),
                    "original_query": search_results.get("original_query"),
                    "expanded_query": search_results.get("expanded_query"),
                    "total_results": search_results.get("total_results")
                }
                
                logger.info(f"Found {len(context_chunks)} relevant chunks")
            else:
                logger.warning("No relevant chunks found")
        
        # Auto-select model if requested
        if auto_select_model:
            model_name = await self.llm_service.select_best_model(
                query=message,
                document_content=context
            )
            logger.info(f"Auto-selected model: {model_name}")
        
        # Generate response using LLM with context
        logger.info(f"Generating response with model: {model_name}")
        response_text = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=message,
            model_name=model_name,
            context=context
        )
        
        # Store user message
        user_message = ChatMessage(
            id=uuid4(),
            sender="user",
            content=message,
            attachments=document_ids
        )
        self.db.add(user_message)
        
        # Store AI response with metadata
        ai_content = response_text
        if search_metadata:
            ai_content += f"\n\n[Search: {search_metadata['search_mode']}, Results: {search_metadata['total_results']}]"
        
        ai_message = ChatMessage(
            id=uuid4(),
            sender="ai",
            content=ai_content,
            attachments=None
        )
        self.db.add(ai_message)
        await self.db.commit()
        await self.db.refresh(ai_message)
        
        logger.info(f"Chat message {ai_message.id} saved successfully")
        
        return ChatResponse(
            id=ai_message.id,
            session_id=ai_message.chat_id,
            sender="ai",
            content=response_text,  # Without metadata for display
            created_at=ai_message.timestamp
        )

    async def _handle_comparison_query(
        self,
        user_id: str,
        message: str,
        document_ids: List[str],
        model_name: str
    ) -> ChatResponse:
        """
        Handle multi-document comparison queries.
        """
        from app.services.comparison_service import ComparisonService
        
        logger.info(f"Handling comparison query for {len(document_ids)} documents")
        
        comparison_service = ComparisonService(self.db, self.llm_service)
        
        # Determine what to compare based on query
        if "methodology" in message.lower() or "method" in message.lower():
            result = await comparison_service.compare_methodologies(document_ids)
            response_text = f"**Methodology Comparison:**\n\n{result['analysis']}"
        
        elif "gap" in message.lower() or "limitation" in message.lower():
            result = await comparison_service.identify_research_gaps(document_ids)
            response_text = f"**Research Gaps Analysis:**\n\n{result['analysis']}"
        
        else:
            # General comparison
            result = await comparison_service.compare_documents(
                document_ids=document_ids,
                comparison_aspects=['objectives', 'methodology', 'findings'],
                include_contradictions=True
            )
            
            # Format comparison table
            table = result.get('comparison_table', {})
            response_text = f"**Document Comparison:**\n\n"
            response_text += f"Compared {result['total_documents']} documents\n\n"
            
            # Add synthesis
            response_text += f"**Overall Synthesis:**\n{result['overall_synthesis']}\n\n"
            
            # Add agreements/contradictions if available
            if result.get('agreements_contradictions'):
                response_text += f"**Key Insights:**\n{result['agreements_contradictions']['analysis']}"
        
        # Store messages
        user_message = ChatMessage(
            id=uuid4(),
            sender="user",
            content=message,
            attachments=document_ids
        )
        self.db.add(user_message)
        
        ai_message = ChatMessage(
            id=uuid4(),
            sender="ai",
            content=response_text,
            attachments=None
        )
        self.db.add(ai_message)
        await self.db.commit()
        await self.db.refresh(ai_message)
        
        return ChatResponse(
            id=ai_message.id,
            session_id=ai_message.chat_id,
            sender="ai",
            content=response_text,
            created_at=ai_message.timestamp
        )

    async def _handle_summarization_query(
        self,
        user_id: str,
        message: str,
        document_ids: List[str],
        model_name: str,
        summary_type: Optional[str]
    ) -> ChatResponse:
        """
        Handle document summarization requests.
        """
        logger.info(f"Handling summarization query for {len(document_ids)} documents")
        
        # Auto-detect summary type from query if not provided
        if not summary_type:
            message_lower = message.lower()
            if "brief" in message_lower or "short" in message_lower:
                summary_type = "short"
            elif "detailed" in message_lower or "comprehensive" in message_lower:
                summary_type = "detailed"
            elif "bullet" in message_lower or "points" in message_lower:
                summary_type = "bullet"
            elif "section" in message_lower:
                summary_type = "section"
            else:
                summary_type = "short"  # Default
        
        logger.info(f"Using summary type: {summary_type}")
        
        # Get document content
        all_chunks = []
        for doc_id in document_ids:
            chunks = await self.doc_service.search_similar_chunks(
                query="summary main points key findings",
                doc_ids=[doc_id],
                top_k=10
            )
            all_chunks.extend(chunks)
        
        content = "\n\n".join(all_chunks)
        
        # Generate summary
        summary = await self.llm_service.generate_summary(
            content=content,
            summary_type=summary_type,
            model_name=model_name
        )
        
        response_text = f"**{summary_type.title()} Summary:**\n\n{summary}"
        
        # Store messages
        user_message = ChatMessage(
            id=uuid4(),
            sender="user",
            content=message,
            attachments=document_ids
        )
        self.db.add(user_message)
        
        ai_message = ChatMessage(
            id=uuid4(),
            sender="ai",
            content=response_text,
            attachments=None
        )
        self.db.add(ai_message)
        await self.db.commit()
        await self.db.refresh(ai_message)
        
        return ChatResponse(
            id=ai_message.id,
            session_id=ai_message.chat_id,
            sender="ai",
            content=response_text,
            created_at=ai_message.timestamp
        )

    def _classify_query_intent(self, message: str) -> str:
        """
        Classify the intent of user's query.
        
        Returns: "comparison", "summarization", "question", "general"
        """
        message_lower = message.lower()
        
        # Comparison indicators
        comparison_keywords = [
            "compare", "difference", "vs", "versus", "contrast",
            "similar", "common", "disagree", "agree"
        ]
        if any(keyword in message_lower for keyword in comparison_keywords):
            return "comparison"
        
        # Summarization indicators
        summary_keywords = [
            "summarize", "summary", "sum up", "overview",
            "key points", "main ideas", "brief"
        ]
        if any(keyword in message_lower for keyword in summary_keywords):
            return "summarization"
        
        # Question indicators
        question_keywords = ["what", "how", "why", "when", "where", "who", "explain"]
        if any(keyword in message_lower for keyword in question_keywords):
            return "question"
        
        return "general"

    # ==============================
    # EXISTING METHODS (Unchanged)
    # ==============================

    async def get_user_chat_history(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatResponse]:
        """
        Get chat history for a user in reverse chronological order
        """
        query = await self.db.execute(
            select(ChatMessage)
            .order_by(ChatMessage.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        messages = query.scalars().all()
        
        return [
            ChatResponse(
                id=m.id,
                session_id=m.chat_id,
                sender=m.sender,
                content=m.content,
                created_at=m.timestamp
            ) for m in messages
        ]

    async def delete_chat(
        self,
        chat_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a chat message by ID
        """
        chat_uuid = UUID(chat_id) if isinstance(chat_id, str) else chat_id
        
        query = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == chat_uuid)
        )
        message = query.scalar_one_or_none()
        
        if not message:
            return False

        await self.db.delete(message)
        await self.db.commit()
        logger.info(f"Chat message {chat_id} deleted")
        return True