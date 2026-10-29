from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str
    modality: str = "text"
    created_at: Optional[str] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User text input")
    conversation_id: Optional[str] = Field(None, description="Existing conversation UUID")
    mode: str = Field("standard", description="Chat mode: 'standard', 'emotional', or 'rag'")
    search_enabled: bool = Field(False, description="Whether to trigger external web search")
    voice_response: bool = Field(False, description="Whether to generate TTS audio response")
    document_id: Optional[str] = Field(None, description="Active or attached document ID for direct document QA")

class SourceReference(BaseModel):
    title: str
    source_type: str  # "web" or "document"
    url_or_file: str
    snippet: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    modality: str = "text"
    sources: List[SourceReference] = []
    audio_base64: Optional[str] = None
    crisis_flag: bool = False
    provider_used: Optional[str] = None
    image_url: Optional[str] = None

class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=1000)
    conversation_id: Optional[str] = None
