# app/services/note_service.py
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models import note as note_model
from app.models import document as document_model
from app.schemas import note as note_schema


class NoteService:
    """
    Service to manage notes created by users.
    Notes can be linked to documents and optionally used for analytics or LLM context.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------
    # Create a new note
    # ------------------------------
    async def create_note(
        self,
        user_id: str,
        title: str,
        content: str,
        document_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_pinned: bool = False
    ) -> note_schema.NoteResponse:
        """
        Create a new note with optional tags and pinned status
        """
        # Convert string UUIDs to UUID objects
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        doc_uuid = UUID(document_id) if document_id and isinstance(document_id, str) else document_id
        
        # Check if document exists
        if doc_uuid:
            doc = await self.db.get(document_model.Document, doc_uuid)
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

        note_entry = note_model.Note(
            user_id=user_uuid,
            document_id=doc_uuid,
            title=title,
            content=content,
            tags=tags or [],
            is_pinned=is_pinned
        )
        self.db.add(note_entry)
        await self.db.commit()
        await self.db.refresh(note_entry)

        return note_schema.NoteResponse(
            id=note_entry.id,
            user_id=note_entry.user_id,
            document_id=note_entry.document_id,
            title=note_entry.title,
            content=note_entry.content,
            tags=note_entry.tags or [],
            is_pinned=note_entry.is_pinned,
            created_at=note_entry.created_at,
            updated_at=note_entry.updated_at
        )

    # ------------------------------
    # Update an existing note
    # ------------------------------
    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_pinned: Optional[bool] = None
    ) -> note_schema.NoteResponse:
        """
        Update an existing note with optional fields
        """
        # Convert string UUID to UUID object
        note_uuid = UUID(note_id) if isinstance(note_id, str) else note_id
        
        note_entry = await self.db.get(note_model.Note, note_uuid)
        if not note_entry:
            raise HTTPException(status_code=404, detail="Note not found")

        if title is not None:
            note_entry.title = title
        if content is not None:
            note_entry.content = content
        if tags is not None:
            note_entry.tags = tags
        if is_pinned is not None:
            note_entry.is_pinned = is_pinned

        self.db.add(note_entry)
        await self.db.commit()
        await self.db.refresh(note_entry)

        return note_schema.NoteResponse(
            id=note_entry.id,
            user_id=note_entry.user_id,
            document_id=note_entry.document_id,
            title=note_entry.title,
            content=note_entry.content,
            tags=note_entry.tags or [],
            is_pinned=note_entry.is_pinned,
            created_at=note_entry.created_at,
            updated_at=note_entry.updated_at
        )

    # ------------------------------
    # Delete a note
    # ------------------------------
    async def delete_note(self, note_id: str) -> bool:
        """
        Delete a note by ID
        """
        # Convert string UUID to UUID object
        note_uuid = UUID(note_id) if isinstance(note_id, str) else note_id
        
        note_entry = await self.db.get(note_model.Note, note_uuid)
        if not note_entry:
            raise HTTPException(status_code=404, detail="Note not found")

        await self.db.delete(note_entry)
        await self.db.commit()
        return True

    # ------------------------------
    # Fetch notes for a user
    # ------------------------------
    async def get_user_notes(
        self,
        user_id: str,
        document_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[note_schema.NoteResponse]:
        """
        Get all notes for a user with optional document filter and pagination
        """
        # Convert string UUIDs to UUID objects
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        doc_uuid = UUID(document_id) if document_id and isinstance(document_id, str) else document_id
        
        stmt = select(note_model.Note).where(note_model.Note.user_id == user_uuid)
        if doc_uuid:
            stmt = stmt.where(note_model.Note.document_id == doc_uuid)
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        notes = result.scalars().all()

        return [
            note_schema.NoteResponse(
                id=n.id,
                user_id=n.user_id,
                document_id=n.document_id,
                title=n.title,
                content=n.content,
                tags=n.tags or [],
                is_pinned=n.is_pinned,
                created_at=n.created_at,
                updated_at=n.updated_at
            )
            for n in notes
        ]