from pydantic import BaseModel, Field
from typing import List, Optional, Union
from uuid import UUID
from datetime import datetime

class ChatMessageBase(BaseModel):
    sender: str = Field(..., example="user")
    content: str = Field(..., example="Hello AI, analyze this document")
    attachments: Optional[List[str]] = Field(None, example=["file1.pdf", "file2.docx"])

class ChatMessageCreate(ChatMessageBase):
    chat_id: Optional[UUID] = None

class ChatMessageRead(ChatMessageBase):
    id: UUID
    timestamp: datetime
    chat_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    attachments: Optional[List[str]] = None

ChatMessageResponse = ChatMessageRead

class ChatRequest(BaseModel):
    message: str = Field(..., example="Summarize this document")
    document_ids: Optional[List[Union[UUID, str]]] = None  # Accept both UUID and string
    model_name: Optional[str] = Field("llama", example="llama")

class ChatResponse(BaseModel):
    id: UUID
    session_id: Optional[UUID] = None
    sender: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True