from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    current_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentVersionResponse(BaseModel):
    id: str
    document_id: str
    version_number: int
    content: str
    change_summary: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentCreateRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)

class DocumentUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    change_summary: Optional[str] = "Manual update"

class DocumentAIEditRequest(BaseModel):
    action: str = Field(..., description="Action: 'summarize', 'grammar', 'expand', or 'custom'")
    custom_instruction: Optional[str] = None
