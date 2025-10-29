# app/schemas/note.py
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class NoteBase(BaseModel):
    title: str = Field(..., example="Key Insights from Meeting")
    content: str = Field(..., example="# Meeting Notes\n- Item 1\n- Item 2")
    tags: Optional[List[str]] = Field(default_factory=list)
    is_pinned: Optional[bool] = False


class NoteCreate(NoteBase):
    document_id: Optional[UUID] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None


class NoteRead(NoteBase):
    id: UUID
    user_id: UUID  # Changed from str to UUID
    document_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alias for responses
NoteResponse = NoteRead