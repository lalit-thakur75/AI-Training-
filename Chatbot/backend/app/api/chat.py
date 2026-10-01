from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.schemas import ChatResponse
from app.services.llm_service import generate_chat_response
from typing import Optional

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    conversation_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Construct message list for LLM
    # In a full implementation, we would fetch conversation history from the DB here
    messages = [
        {"role": "system", "content": "You are a supportive, empathetic multimodal AI chatbot. Help the user concisely and friendly."},
        {"role": "user", "content": message}
    ]
    
    # Call the Groq LLM
    answer = generate_chat_response(messages)
    
    return ChatResponse(
        answer=answer,
        modality="text",
        sources=[],
        conversation_id=conversation_id or 1
    )
