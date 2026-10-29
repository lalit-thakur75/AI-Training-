import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse, SourceReference, GenerateImageRequest
from app.services.llm_service import LLMService
from app.services.vision_service import VisionService
from app.services.speech_service import SpeechService
from app.services.search_service import SearchService
from app.services.rag_service import RAGService
from app.services.emotional_support_service import (
    check_for_crisis,
    EMOTIONAL_SYSTEM_PROMPT
)
from app.config import settings

from app.models.chunk import DocumentChunk
from app.services.image_gen_service import ImageGenService

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main chat endpoint handling text interactions, emotional support,
    crisis interception (112 emergency), web search, and RAG document grounding.
    """
    # 1. Ensure or retrieve conversation
    conv_id = request.conversation_id
    if conv_id:
        conv = await db.get(Conversation, conv_id)
        if not conv:
            conv = Conversation(id=conv_id, title=request.message[:40])
            db.add(conv)
            await db.commit()
    else:
        conv = Conversation(title=request.message[:40])
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    # 2. Check for emotional crisis keywords first (deterministic safety shield)
    is_crisis, crisis_reply = check_for_crisis(request.message)
    if is_crisis:
        # Record user message and crisis response
        user_msg = Message(conversation_id=conv_id, role="user", content=request.message, modality="text")
        asst_msg = Message(conversation_id=conv_id, role="assistant", content=crisis_reply, modality="text")
        db.add_all([user_msg, asst_msg])
        await db.commit()

        # Generate audio if requested
        audio_b64 = None
        if request.voice_response:
            audio_b64 = await SpeechService.text_to_speech(crisis_reply)

        return ChatResponse(
            conversation_id=conv_id,
            reply=crisis_reply,
            modality="text",
            sources=[],
            audio_base64=audio_b64,
            crisis_flag=True
        )

    # 2b. Natural language image generation intent
    msg_lower = request.message.lower().strip()
    img_triggers = [
        "generate image", "create image", "make an image", "image of",
        "draw a", "draw an", "image banao", "tasveer banao", "picture banao",
        "generate an image", "generate a picture"
    ]
    if any(msg_lower.startswith(t) or f" {t} " in f" {msg_lower} " for t in img_triggers):
        gen_prompt = request.message
        for t in img_triggers:
            if msg_lower.startswith(t):
                gen_prompt = request.message[len(t):].strip(": ,-")
                break
        if not gen_prompt:
            gen_prompt = request.message

        try:
            gen_result = await ImageGenService.generate_image(gen_prompt)
            img_url = gen_result["image_url"]
            provider = gen_result["provider"]
            reply_text = f"🎨 Here is your generated image for: **{gen_prompt}**"

            user_msg = Message(conversation_id=conv_id, role="user", content=request.message, modality="text")
            asst_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=reply_text,
                modality="image",
                extra_metadata={"image_url": img_url, "provider_used": provider}
            )
            db.add_all([user_msg, asst_msg])
            await db.commit()

            return ChatResponse(
                conversation_id=conv_id,
                reply=reply_text,
                modality="image",
                image_url=img_url,
                provider_used=provider
            )
        except Exception as e:
            # Fall back to standard LLM chat if generation fails
            pass

    # 3. Retrieve conversation history for context
    history_query = (
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
        .limit(10)
    )
    history_records = (await db.execute(history_query)).scalars().all()
    chat_history = [{"role": m.role, "content": m.content} for m in history_records]
    chat_history.append({"role": "user", "content": request.message})

    # 4. Context preparation (Web Search & RAG)
    sources = []
    context_parts = []

    # Emotional mode: empathetic prompt, strictly avoid leaking to external search
    if request.mode == "emotional":
        system_prompt = EMOTIONAL_SYSTEM_PROMPT
    else:
        system_prompt = "You are a knowledgeable, friendly, and practical Multimodal AI Assistant."

    # RAG Document Search: Check if document_id is provided, or mode is 'rag', or chunks exist
    should_rag = bool(request.document_id) or request.mode == "rag" or "document" in request.message.lower() or "pdf" in request.message.lower()
    if not should_rag and request.mode != "emotional":
        has_chunks = (await db.execute(select(DocumentChunk.id).limit(1))).scalars().first()
        if has_chunks is not None:
            should_rag = True

    if should_rag:
        matching_chunks, doc_sources = await RAGService.search_similar_chunks(
            db, 
            request.message, 
            top_k=settings.RAG_TOP_K,
            document_id=request.document_id
        )
        if matching_chunks and (request.document_id or request.mode == "rag" or matching_chunks[0].get("similarity", 0) > 0.15):
            context_parts.append(RAGService.format_rag_context(matching_chunks))
            sources.extend(doc_sources)

    # Web Search (triggered if search_enabled toggle is ON or explicit search query, and not in emotional mode)
    should_search = (
        request.search_enabled 
        or "search the web" in request.message.lower() 
        or "search web" in request.message.lower()
        or request.message.lower().startswith("search ")
    ) and request.mode != "emotional"

    if should_search:
        clean_search_query = request.message
        for prefix in ["search the web for", "search the web:", "search web:", "search:"]:
            if clean_search_query.lower().startswith(prefix):
                clean_search_query = clean_search_query[len(prefix):].strip()
        web_sources = await SearchService.search_web_async(clean_search_query, max_results=3)
        if web_sources:
            context_parts.append(SearchService.build_search_context(web_sources))
            sources.extend(web_sources)

    combined_context = "\n\n".join(context_parts) if context_parts else None

    # 5. Generate Response via LLM with provider fallback
    reply, provider_used = await LLMService.generate_response_with_meta(
        messages=chat_history,
        system_prompt=system_prompt,
        context_str=combined_context
    )

    # 6. Save messages to DB
    user_msg = Message(conversation_id=conv_id, role="user", content=request.message, modality="text")
    asst_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=reply,
        modality="text",
        extra_metadata={"sources": [s.model_dump() for s in sources], "provider_used": provider_used}
    )
    db.add_all([user_msg, asst_msg])
    await db.commit()

    # 7. Optional Text-to-Speech audio generation
    audio_b64 = None
    if request.voice_response:
        audio_b64 = await SpeechService.text_to_speech(reply)

    return ChatResponse(
        conversation_id=conv_id,
        reply=reply,
        modality="text",
        sources=sources,
        audio_base64=audio_b64,
        crisis_flag=False,
        provider_used=provider_used
    )


@router.post("/voice", response_model=ChatResponse)
async def chat_voice(
    audio: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    mode: str = Form("standard"),
    search_enabled: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts speech audio recording/upload, transcribes it,
    processes it through the AI pipeline, and returns text + voice response.
    """
    ext = os.path.splitext(audio.filename)[1].lower() if audio.filename else ".wav"
    safe_audio_name = f"voice_{uuid.uuid4()}{ext}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    audio_path = os.path.join(settings.UPLOAD_DIR, safe_audio_name)

    # Save audio temporarily
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # Transcribe speech to text
    transcribed_text = await SpeechService.transcribe_audio(audio_path)

    # Clean up temporary audio file
    if os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except Exception:
            pass

    if not transcribed_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio.")

    # Process transcribed question via main chat pipeline
    chat_req = ChatRequest(
        message=transcribed_text,
        conversation_id=conversation_id,
        mode=mode,
        search_enabled=search_enabled,
        voice_response=True
    )
    return await chat(chat_req, db)


@router.post("/image", response_model=ChatResponse)
async def chat_image(
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(""),
    conversation_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts an image and user question, runs image understanding,
    and returns an AI visual analysis response.
    """
    # Validate extension and size
    file_bytes = await image.read()
    if not VisionService.is_valid_image(image.filename, len(file_bytes)):
        raise HTTPException(
            status_code=400,
            detail="Invalid image. Supported formats: JPG, PNG, WEBP. Max size: 10MB."
        )

    # Save image safely
    ext = os.path.splitext(image.filename)[1].lower()
    safe_image_name = f"img_{uuid.uuid4()}{ext}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    image_path = os.path.join(settings.UPLOAD_DIR, safe_image_name)

    with open(image_path, "wb") as f:
        f.write(file_bytes)

    # Run vision analysis with OCR and question answering
    user_prompt = prompt.strip() if prompt else "Describe this image in detail and extract all text and details."
    analysis_prompt = (
        f"User request: '{user_prompt}'\n\n"
        "Instructions:\n"
        "1. Carefully examine the entire image, including all text, questions, diagrams, or paragraphs.\n"
        "2. If the user asked a question or asked to solve/explain something in the image, provide the direct, accurate answer or solution.\n"
        "3. If the user asked to summarize a paragraph or document in the image, provide a structured, high-quality summary.\n"
        "4. Be clear, thorough, and helpful."
    )
    analysis_result, provider_used = await VisionService.analyze_image_with_meta(image_path, analysis_prompt)

    sources = []
    # If the user explicitly asks for web search or current information
    if any(k in user_prompt.lower() for k in ["search", "web", "latest", "news", "current", "google"]):
        try:
            web_sources = await SearchService.search_web_async(user_prompt, max_results=3)
            if web_sources:
                sources.extend(web_sources)
                search_ctx = SearchService.build_search_context(web_sources)
                synth_prompt = (
                    f"Visual Image Context:\n{analysis_result}\n\n"
                    f"{search_ctx}\n\n"
                    f"User Question: {user_prompt}\n\n"
                    "Provide a synthesized, highly accurate answer incorporating both the visual analysis and the web search facts."
                )
                synth_reply, _ = await LLMService.generate_response_with_meta(
                    messages=[{"role": "user", "content": synth_prompt}]
                )
                if synth_reply:
                    analysis_result = synth_reply
        except Exception as e:
            logger.warning(f"Image web search error: {e}")

    # Manage conversation
    conv_id = conversation_id
    if conv_id:
        conv = await db.get(Conversation, conv_id)
        if not conv:
            conv = Conversation(id=conv_id, title=f"Image: {image.filename[:30]}")
            db.add(conv)
            await db.commit()
    else:
        conv = Conversation(title=f"Image: {image.filename[:30]}")
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    # Record messages
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=f"[Attached Image: {image.filename}] {user_prompt}",
        modality="image",
        extra_metadata={"filename": image.filename, "storage_path": image_path}
    )
    asst_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=analysis_result,
        modality="text",
        extra_metadata={"sources": [s.model_dump() for s in sources], "provider_used": provider_used}
    )
    db.add_all([user_msg, asst_msg])
    await db.commit()

    return ChatResponse(
        conversation_id=conv_id,
        reply=analysis_result,
        modality="image",
        sources=sources,
        audio_base64=None,
        crisis_flag=False,
        provider_used=provider_used
    )

@router.post("/generate-image", response_model=ChatResponse)
async def generate_image_endpoint(
    request: GenerateImageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates an image from prompt using DALL-E / FLUX / Pollinations and returns image URL.
    """
    conv_id = request.conversation_id
    if conv_id:
        conv = await db.get(Conversation, conv_id)
        if not conv:
            conv = Conversation(id=conv_id, title=f"Generated Image: {request.prompt[:30]}")
            db.add(conv)
            await db.commit()
    else:
        conv = Conversation(title=f"Generated Image: {request.prompt[:30]}")
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    try:
        gen_result = await ImageGenService.generate_image(request.prompt)
        img_url = gen_result["image_url"]
        provider = gen_result["provider"]
        reply_text = f"🎨 Here is your generated image for: **{request.prompt}**"

        user_msg = Message(
            conversation_id=conv_id,
            role="user",
            content=f"Generate image: {request.prompt}",
            modality="text"
        )
        asst_msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content=reply_text,
            modality="image",
            extra_metadata={"image_url": img_url, "provider_used": provider}
        )
        db.add_all([user_msg, asst_msg])
        await db.commit()

        return ChatResponse(
            conversation_id=conv_id,
            reply=reply_text,
            modality="image",
            image_url=img_url,
            provider_used=provider
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """
    Returns list of all stored conversations ordered by most recently updated.
    """
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)
    )
    convs = result.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in convs
    ]

@router.get("/conversations/{conv_id}")
async def get_conversation_history(conv_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns conversation details and full message history for the given conversation ID.
    """
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at)
    )
    records = result.scalars().all()
    return {
        "id": conv.id,
        "title": conv.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "modality": m.modality,
                "sources": (m.extra_metadata or {}).get("sources", []),
                "image_url": (m.extra_metadata or {}).get("image_url"),
                "audio_base64": (m.extra_metadata or {}).get("audio_base64"),
                "provider_used": (m.extra_metadata or {}).get("provider_used"),
                "created_at": m.created_at.strftime("%I:%M %p") if m.created_at else None
            }
            for m in records
        ]
    }

@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes a conversation and its messages from the database.
    """
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return {"status": "deleted", "id": conv_id}
