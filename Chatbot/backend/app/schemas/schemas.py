from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str
    modality: str = "text"

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    filename: str
    file_type: str
    content: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    version: int

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    # Assuming attached files and media are handled via multipart/form-data if they are new,
    # or by ID if already uploaded. For MVP, we can keep it simple.

class ChatResponse(BaseModel):
    answer: str
    modality: str
    sources: List[str] = []
    conversation_id: int

class SearchRequest(BaseModel):
    query: str

class TTSRequest(BaseModel):
    text: str
