# app/api/v1/notes_routes.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import note as note_schema
from app.services.note_service import NoteService
from app.services.auth_service import AuthService
from app.db.session import get_db

router = APIRouter(prefix="/notes", tags=["notes"])

# ------------------------------
# Create a new note
# ------------------------------
@router.post("/", response_model=note_schema.NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_request: note_schema.NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Create a new note for the current user.
    
    - **title**: Title of the note
    - **content**: Content/body of the note
    - **tags**: Optional list of tags
    - **is_pinned**: Optional boolean to pin the note
    - **document_id**: Optional UUID of associated document
    """
    note_service = NoteService(db)
    note = await note_service.create_note(
        user_id=str(current_user.id),
        title=note_request.title,
        content=note_request.content,
        tags=note_request.tags,
        is_pinned=note_request.is_pinned,
        document_id=str(note_request.document_id) if note_request.document_id else None
    )
    return note

# ------------------------------
# Update an existing note
# ------------------------------
@router.put("/{note_id}", response_model=note_schema.NoteResponse)
async def update_note(
    note_id: UUID = Path(..., description="UUID of the note to update"),
    note_request: note_schema.NoteUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Update an existing note.
    
    All fields are optional - only provided fields will be updated.
    """
    note_service = NoteService(db)
    note = await note_service.update_note(
        note_id=str(note_id),
        title=note_request.title,
        content=note_request.content,
        tags=note_request.tags,
        is_pinned=note_request.is_pinned
    )
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note

# ------------------------------
# Delete a note
# ------------------------------
@router.delete("/{note_id}", response_model=dict)
async def delete_note(
    note_id: UUID = Path(..., description="UUID of the note to delete"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Delete a note by its UUID.
    """
    note_service = NoteService(db)
    success = await note_service.delete_note(note_id=str(note_id))
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return {"detail": "Note deleted successfully"}

# ------------------------------
# Get a single note by ID
# ------------------------------
@router.get("/{note_id}", response_model=note_schema.NoteResponse)
async def get_note(
    note_id: UUID = Path(..., description="UUID of the note to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Get a single note by its UUID.
    """
    note_service = NoteService(db)
    notes = await note_service.get_user_notes(
        user_id=str(current_user.id),
        skip=0,
        limit=1
    )
    
    # Filter to find the specific note
    note = next((n for n in notes if str(n.id) == str(note_id)), None)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note

# ------------------------------
# Fetch user notes with optional document filter and pagination
# ------------------------------
@router.get("/", response_model=List[note_schema.NoteResponse])
async def get_user_notes(
    document_id: Optional[UUID] = Query(None, description="Filter notes by document UUID"),
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notes to return"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Get all notes for the current user.
    
    Can be filtered by document_id and supports pagination.
    """
    note_service = NoteService(db)
    notes = await note_service.get_user_notes(
        user_id=str(current_user.id),
        document_id=str(document_id) if document_id else None,
        skip=skip,
        limit=limit
    )
    return notes