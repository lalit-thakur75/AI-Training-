from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db, engine
from app.config import settings
from app.schemas.health import HealthResponse
from app.services.ai_router import ai_router

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint reporting API, database, and AI service configuration status."""
    db_status = {
        "connected": False,
        "type": "unknown",
        "pgvector": False,
        "error": None
    }

    try:
        # Check database connectivity
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status["connected"] = True
            dialect = engine.dialect.name
            db_status["type"] = dialect

            # Check for pgvector if postgresql
            if dialect == "postgresql":
                try:
                    vec_check = await db.execute(
                        text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                    )
                    db_status["pgvector"] = vec_check.scalar() == 1
                except Exception:
                    db_status["pgvector"] = False
    except Exception as e:
        db_status["error"] = str(e)

    # Determine overall status
    any_provider_configured = any(p.is_configured for p in ai_router.providers.values())
    if db_status["connected"]:
        overall = "healthy"
    elif any_provider_configured:
        overall = "degraded"
    else:
        overall = "unavailable"

    return HealthResponse(
        status=overall,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        database=db_status,
        configured_providers={
            "priority": settings.PROVIDER_PRIORITY,
            "openai_configured": ai_router.providers["openai"].is_configured,
            "gemini_configured": ai_router.providers["gemini"].is_configured,
            "xai_configured": ai_router.providers["xai"].is_configured,
            "huggingface_configured": ai_router.providers["huggingface"].is_configured,
            "embeddings": f"{settings.EMBEDDING_PROVIDER} ({settings.EMBEDDING_MODEL})",
            "search": settings.SEARCH_PROVIDER,
            "tts": f"{settings.TTS_PROVIDER} ({settings.TTS_VOICE})",
            "stt": settings.STT_PROVIDER
        }
    )

@router.get("/providers/status")
async def provider_status():
    """
    Returns safe configuration status for all 4 AI providers without exposing secrets.
    """
    statuses = []
    for name in settings.priority_list:
        p = ai_router.get_provider(name)
        if p:
            statuses.append({
                "name": p.name,
                "model": p.model_name,
                "configured": p.is_configured,
                "supports_vision": p.supports_vision
            })
    return {"priority": settings.priority_list, "providers": statuses}

@router.get("/providers/diagnostics")
async def provider_diagnostics():
    """
    Executes a safe, lightweight authenticated connectivity test for all configured providers.
    """
    return await ai_router.get_diagnostics()
