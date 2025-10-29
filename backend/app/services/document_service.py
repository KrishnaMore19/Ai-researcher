# app/services/document_service.py
import os
import logging
from typing import List, Optional, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import UploadFile, HTTPException
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.models.document import Document
from app.schemas.document import DocumentRead, DocumentCreate
from app.utils.file_handler import save_upload_file, move_file, delete_file, read_file_content
from app.utils.pdf_extractor import extract_text_from_pdf
from app.utils.chunker import split_text_into_chunks
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_DIR
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )

    # ------------------------------
    # CREATE / UPLOAD DOCUMENT
    # ------------------------------
    async def create_document(
        self, 
        user_id: str, 
        title: str, 
        file_path: str,
        file_type: str = None,
        file_size: str = None
    ) -> DocumentRead:
        """Create a new document record and generate embeddings for ChromaDB"""
        if not file_type:
            file_type = os.path.splitext(file_path)[1].replace('.', '').upper()
        
        if not file_size:
            file_size = self._get_file_size(file_path)
        
        filename = os.path.basename(file_path)
        
        # Create DB entry
        new_doc = Document(
            name=filename,
            type=file_type,
            size=file_size,
            status="processing"
        )
        self.db.add(new_doc)
        await self.db.commit()
        await self.db.refresh(new_doc)
        
        # Extract text and generate embeddings
        try:
            await self._generate_embeddings(new_doc.id, file_path, file_type)
            new_doc.status = "completed"
            self.db.add(new_doc)
            await self.db.commit()
            logger.info(f"Document {new_doc.id} embeddings generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate embeddings for {new_doc.id}: {e}")
            new_doc.status = "failed"
            self.db.add(new_doc)
            await self.db.commit()

        return DocumentRead(
            id=new_doc.id,
            name=new_doc.name,
            type=new_doc.type,
            size=new_doc.size,
            uploaded_date=new_doc.uploaded_date,
            status=new_doc.status,
            is_active=new_doc.is_active
        )

    # ------------------------------
    # Helper: Generate embeddings and store in ChromaDB
    # ------------------------------
    async def _generate_embeddings(self, doc_id, file_path: str, file_type: str):
        """Extract text from document, split into chunks, and store embeddings in ChromaDB"""
        # Extract text from file
        text_content = self._extract_text(file_path, file_type)
        
        if not text_content:
            raise Exception("Could not extract text from document")
        
        # Split into chunks
        chunks = split_text_into_chunks(
            text_content,
            chunk_size=1000,
            overlap=200
        )
        
        logger.info(f"Document {doc_id} split into {len(chunks)} chunks")
        
        # Add chunks to ChromaDB with metadata
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{idx}"
            
            self.collection.add(
                documents=[chunk],
                metadatas=[{
                    "doc_id": str(doc_id),
                    "chunk_index": idx,
                    "filename": os.path.basename(file_path)
                }],
                ids=[chunk_id]
            )
        
        logger.info(f"Added {len(chunks)} chunks to ChromaDB for document {doc_id}")

    # ------------------------------
    # Helper: Extract text from file
    # ------------------------------
    def _extract_text(self, file_path: str, file_type: str) -> Optional[str]:
        """Extract text content from PDF or text files"""
        try:
            if file_type.upper() == 'PDF':
                with open(file_path, 'rb') as f:
                    pdf_content = f.read()
                return extract_text_from_pdf(pdf_content)
            else:
                return read_file_content(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None

    # ------------------------------
    # GET DOCUMENT BY ID
    # ------------------------------
    async def get_document(
        self, document_id: str, user_id: str
    ) -> Optional[DocumentRead]:
        """Get a single document by ID"""
        query = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.is_active == True
            )
        )
        doc = query.scalar_one_or_none()
        if not doc:
            return None
        
        return DocumentRead(
            id=doc.id,
            name=doc.name,
            type=doc.type,
            size=doc.size,
            uploaded_date=doc.uploaded_date,
            status=doc.status,
            is_active=doc.is_active
        )

    # ------------------------------
    # GET ALL DOCUMENTS OF USER
    # ------------------------------
    async def get_documents(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[DocumentRead]:
        """Get all documents for a user with pagination"""
        query = await self.db.execute(
            select(Document)
            .where(Document.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        docs = query.scalars().all()
        
        return [
            DocumentRead(
                id=doc.id,
                name=doc.name,
                type=doc.type,
                size=doc.size,
                uploaded_date=doc.uploaded_date,
                status=doc.status,
                is_active=doc.is_active
            ) for doc in docs
        ]

    # ------------------------------
    # DELETE DOCUMENT
    # ------------------------------
    async def delete_document(
        self, document_id: str, user_id: str
    ) -> bool:
        """Soft delete a document and remove embeddings from ChromaDB"""
        query = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = query.scalar_one_or_none()
        if not doc:
            return False

        # Remove embeddings from ChromaDB
        try:
            results = self.collection.get(
                where={"doc_id": str(document_id)}
            )
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks from ChromaDB")
        except Exception as e:
            logger.error(f"Error deleting embeddings from ChromaDB: {e}")

        # Soft delete in database
        doc.is_active = False
        self.db.add(doc)
        await self.db.commit()
        return True

    # ==============================
    # 🆕 ADVANCED SEARCH FEATURES
    # ==============================

    async def search_similar_chunks_advanced(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        search_mode: str = "semantic",  # semantic, hybrid, keyword
        top_k: int = 5,
        expand_query: bool = True
    ) -> Dict[str, any]:
        """
        ADVANCED SEARCH with multiple modes and query expansion
        
        Args:
            query: Search query
            doc_ids: Optional list of document IDs to search within
            search_mode: "semantic" (default), "hybrid", or "keyword"
            top_k: Number of results to return
            expand_query: Whether to expand query with related concepts
        
        Returns:
            Dict with results and metadata
        """
        try:
            logger.info(f"Advanced search: mode={search_mode}, query='{query}'")
            
            # Step 1: Query expansion (optional)
            original_query = query
            if expand_query and search_mode in ["semantic", "hybrid"]:
                expanded = await self._expand_query(query)
                query = expanded
                logger.info(f"Query expanded: '{original_query}' → '{query}'")
            
            # Step 2: Execute search based on mode
            if search_mode == "semantic":
                results = await self._semantic_search(query, doc_ids, top_k)
            elif search_mode == "hybrid":
                results = await self._hybrid_search(query, doc_ids, top_k)
            elif search_mode == "keyword":
                results = await self._keyword_search(query, doc_ids, top_k)
            else:
                raise ValueError(f"Invalid search_mode: {search_mode}")
            
            return {
                "results": results,
                "original_query": original_query,
                "expanded_query": query if expand_query else None,
                "search_mode": search_mode,
                "total_results": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return {
                "results": [],
                "original_query": query,
                "error": str(e)
            }

    async def _expand_query(self, query: str) -> str:
        """
        Expand query with related concepts using LLM
        Example: "ML algorithms" → "machine learning algorithms, neural networks, deep learning"
        """
        # Simple synonym expansion (you can enhance with LLM call)
        synonyms = {
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "nn": "neural network",
            "dl": "deep learning",
            "nlp": "natural language processing"
        }
        
        expanded = query.lower()
        for abbr, full in synonyms.items():
            if abbr in expanded:
                expanded = expanded.replace(abbr, f"{abbr} {full}")
        
        return expanded

    async def _semantic_search(
        self,
        query: str,
        doc_ids: Optional[List[str]],
        top_k: int
    ) -> List[Dict]:
        """Vector-based semantic search using ChromaDB"""
        where_filter = None
        if doc_ids and len(doc_ids) > 0:
            doc_ids_str = [str(doc_id) for doc_id in doc_ids]
            if len(doc_ids_str) == 1:
                where_filter = {"doc_id": doc_ids_str[0]}
            else:
                where_filter = {
                    "$or": [{"doc_id": doc_id} for doc_id in doc_ids_str]
                }
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )
        
        # Format results
        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "relevance_score": 1 - (results["distances"][0][i] / 2) if results.get("distances") else 1.0
                })
        
        return formatted_results

    async def _keyword_search(
        self,
        query: str,
        doc_ids: Optional[List[str]],
        top_k: int
    ) -> List[Dict]:
        """
        Simple keyword-based search (fallback for exact matches)
        Searches within ChromaDB documents for exact keyword matches
        """
        # Get all chunks for specified documents
        where_filter = None
        if doc_ids and len(doc_ids) > 0:
            doc_ids_str = [str(doc_id) for doc_id in doc_ids]
            if len(doc_ids_str) == 1:
                where_filter = {"doc_id": doc_ids_str[0]}
            else:
                where_filter = {
                    "$or": [{"doc_id": doc_id} for doc_id in doc_ids_str]
                }
        
        # Get all chunks
        all_results = self.collection.get(where=where_filter)
        
        # Search for keyword matches
        query_lower = query.lower()
        matches = []
        
        if all_results["documents"]:
            for i, doc in enumerate(all_results["documents"]):
                if query_lower in doc.lower():
                    # Calculate relevance based on term frequency
                    term_frequency = doc.lower().count(query_lower)
                    matches.append({
                        "content": doc,
                        "metadata": all_results["metadatas"][i] if all_results["metadatas"] else {},
                        "term_frequency": term_frequency,
                        "relevance_score": min(term_frequency / 10, 1.0)  # Normalize
                    })
        
        # Sort by relevance and return top_k
        matches.sort(key=lambda x: x["relevance_score"], reverse=True)
        return matches[:top_k]

    async def _hybrid_search(
        self,
        query: str,
        doc_ids: Optional[List[str]],
        top_k: int
    ) -> List[Dict]:
        """
        Hybrid search: Combines semantic + keyword search
        Returns merged results with boosted relevance scores
        """
        # Get semantic results
        semantic_results = await self._semantic_search(query, doc_ids, top_k)
        
        # Get keyword results
        keyword_results = await self._keyword_search(query, doc_ids, top_k)
        
        # Merge results (boost items that appear in both)
        merged = {}
        
        # Add semantic results
        for result in semantic_results:
            content = result["content"]
            merged[content] = {
                **result,
                "semantic_score": result.get("relevance_score", 0.5),
                "keyword_score": 0
            }
        
        # Add/boost keyword results
        for result in keyword_results:
            content = result["content"]
            if content in merged:
                # Boost if found in both
                merged[content]["keyword_score"] = result.get("relevance_score", 0.5)
                merged[content]["relevance_score"] = (
                    merged[content]["semantic_score"] * 0.6 + 
                    result.get("relevance_score", 0) * 0.4
                )
            else:
                merged[content] = {
                    **result,
                    "semantic_score": 0,
                    "keyword_score": result.get("relevance_score", 0.5),
                    "relevance_score": result.get("relevance_score", 0.5) * 0.7
                }
        
        # Sort by relevance and return top_k
        final_results = sorted(
            merged.values(),
            key=lambda x: x["relevance_score"],
            reverse=True
        )[:top_k]
        
        return final_results

    # ------------------------------
    # LEGACY METHOD (kept for backward compatibility)
    # ------------------------------
    async def search_similar_chunks(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[str]:
        """
        Legacy method - returns simple list of chunk strings
        Uses advanced search internally
        """
        advanced_results = await self.search_similar_chunks_advanced(
            query=query,
            doc_ids=doc_ids,
            search_mode="semantic",
            top_k=top_k,
            expand_query=False
        )
        
        # Extract just the content strings for backward compatibility
        return [result["content"] for result in advanced_results.get("results", [])]

    # ------------------------------
    # HELPER METHODS
    # ------------------------------
    def _get_file_size(self, file_path: str) -> str:
        """Get file size in human-readable format"""
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except:
            return "Unknown"
        
