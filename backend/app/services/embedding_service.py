# app/services/embedding_service.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models import document as document_model
from app.models import analytics as analytics_model
from app.schemas import document as document_schema
from app.utils.chunker import split_text_into_chunks
from app.services.llm_service import LLMService
from numpy import dot
from numpy.linalg import norm


class EmbeddingService:
    def __init__(self, db: AsyncSession, llm_service: LLMService):
        self.db = db
        self.llm_service = llm_service

    # ------------------------------
    # Generate embeddings for a document
    # ------------------------------
    async def generate_document_embeddings(
        self, document_id: int, chunk_size: int = 1000, overlap: int = 200
    ) -> List[document_schema.EmbeddingResponse]:
        """
        Generate embeddings for all chunks of a document and save analytics in DB.
        Returns a list of EmbeddingResponse schemas.
        """
        # Fetch document from DB
        query = await self.db.execute(
            document_model.select().where(document_model.Document.id == document_id)
        )
        doc = query.scalars().first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Read document content
        try:
            with open(doc.file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to read document file")

        # Split content into chunks
        chunks = split_text_into_chunks(content, chunk_size=chunk_size, overlap=overlap)
        embeddings_list: List[document_schema.EmbeddingResponse] = []

        # Generate embedding for each chunk
        for chunk in chunks:
            embedding_vector = await self.llm_service.get_embedding(chunk)

            # Optional: store analytics / embeddings in DB
            analytics_entry = analytics_model.DocumentEmbedding(
                document_id=document_id,
                content=chunk,
                embedding=embedding_vector
            )
            self.db.add(analytics_entry)

            # Prepare schema response
            embeddings_list.append(document_schema.EmbeddingResponse(
                document_id=document_id,
                chunk_content=chunk,
                embedding_vector=embedding_vector
            ))

        await self.db.commit()
        return embeddings_list

    # ------------------------------
    # Search for similar document chunks
    # ------------------------------
    async def search_similar_chunks(
        self, query_text: str, top_k: int = 5
    ) -> List[document_schema.SimilarChunkResponse]:
        """
        Search stored document chunks for semantic similarity with a query text.
        Returns a list of SimilarChunkResponse schemas.
        """
        query_embedding = await self.llm_service.get_embedding(query_text)

        # Fetch all embeddings from DB
        all_embeddings_query = await self.db.execute(
            analytics_model.select().where(analytics_model.DocumentEmbedding.embedding != None)
        )
        all_embeddings = all_embeddings_query.scalars().all()

        results: List[document_schema.SimilarChunkResponse] = []

        # Calculate similarity (cosine similarity)
        def cosine_similarity(a, b):
            return float(dot(a, b) / (norm(a) * norm(b)))

        for emb in all_embeddings:
            similarity = cosine_similarity(query_embedding, emb.embedding)
            results.append(document_schema.SimilarChunkResponse(
                document_id=emb.document_id,
                chunk_content=emb.content,
                similarity_score=similarity
            ))

        # Sort by similarity descending and return top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]
