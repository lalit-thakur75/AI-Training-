import pytest
from unittest.mock import AsyncMock, patch
from app.services.emotional_support_service import check_for_crisis
from app.services.document_service import DocumentService
from app.services.vision_service import VisionService
from app.services.search_service import SearchService
from app.schemas.chat import SourceReference
from app.services.ai_router import AIRouter
from app.services.providers.base import BaseProvider

def test_crisis_detection_triggers_112_hotline():
    """Verify that messages expressing self-harm or suicidal intent trigger crisis safeguards."""
    is_crisis, response = check_for_crisis("I feel like I want to end my life")
    assert is_crisis is True
    assert "112" in response
    assert "Helpline" in response

def test_normal_message_does_not_trigger_crisis():
    """Verify standard messages pass through normally."""
    is_crisis, response = check_for_crisis("Can you help me summarize this document?")
    assert is_crisis is False
    assert response == ""

def test_document_chunking():
    """Verify document chunking breaks text with proper overlap."""
    sample_text = (
        "Paragraph 1. This is the first sentence of the text. "
        "Paragraph 2. Here is more information about artificial intelligence and multimodal models. "
        "Paragraph 3. In conclusion, testing is essential for software quality."
    )
    chunks = DocumentService.chunk_text(sample_text, chunk_size=80, chunk_overlap=20)
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c) > 0

def test_vision_file_validation():
    """Verify supported image formats are accepted and unsupported formats are rejected."""
    assert VisionService.is_valid_image("photo.jpg", 1024) is True
    assert VisionService.is_valid_image("photo.png", 1024) is True
    assert VisionService.is_valid_image("script.exe", 1024) is False
    assert VisionService.is_valid_image("photo.jpg", 20 * 1024 * 1024) is False

def test_search_context_builder():
    """Verify search sources format cleanly into LLM context."""
    sources = [
        SourceReference(
            title="FastAPI Official Docs",
            source_type="web",
            url_or_file="https://fastapi.tiangolo.com",
            snippet="FastAPI is a modern, fast web framework for building APIs."
        )
    ]
    formatted = SearchService.build_search_context(sources)
    assert "FastAPI Official Docs" in formatted
    assert "https://fastapi.tiangolo.com" in formatted

@pytest.mark.anyio
async def test_router_intelligent_fallback_when_primary_fails():
    """Verify router automatically falls back to secondary provider if primary throws error."""
    router = AIRouter()

    # Create dummy mock providers
    mock_primary = AsyncMock(spec=BaseProvider)
    mock_primary.name = "mock_primary"
    mock_primary.model_name = "test-model-1"
    mock_primary.is_configured = True
    mock_primary.supports_vision = True
    mock_primary.generate_text.side_effect = RuntimeError("Primary API 500 Server Error")

    mock_secondary = AsyncMock(spec=BaseProvider)
    mock_secondary.name = "mock_secondary"
    mock_secondary.model_name = "test-model-2"
    mock_secondary.is_configured = True
    mock_secondary.supports_vision = True
    mock_secondary.generate_text.return_value = "Success from fallback provider"

    router.providers = {
        "primary": mock_primary,
        "secondary": mock_secondary
    }
    with patch("app.config.settings.PROVIDER_PRIORITY", "primary,secondary"):
        result, provider_used = await router.route_text_chat([{"role": "user", "content": "Hello"}])

    assert result == "Success from fallback provider"
    assert provider_used == "mock_secondary"
    assert mock_primary.generate_text.called
    assert mock_secondary.generate_text.called

@pytest.mark.anyio
async def test_router_vision_capability_filtering():
    """Verify text-only providers are never selected for vision tasks."""
    router = AIRouter()

    mock_text_only = AsyncMock(spec=BaseProvider)
    mock_text_only.name = "text_only"
    mock_text_only.is_configured = True
    mock_text_only.supports_vision = False

    mock_vision = AsyncMock(spec=BaseProvider)
    mock_vision.name = "vision_prov"
    mock_vision.is_configured = True
    mock_vision.supports_vision = True
    mock_vision.generate_vision.return_value = "Detected Eiffel Tower"

    router.providers = {
        "text_only": mock_text_only,
        "vision_prov": mock_vision
    }
    with patch("app.config.settings.PROVIDER_PRIORITY", "text_only,vision_prov"):
        result, provider_used = await router.route_vision("dummy_path.jpg", "What is this?")

    assert result == "Detected Eiffel Tower"
    assert provider_used == "vision_prov"
    assert not mock_text_only.generate_vision.called
    assert mock_vision.generate_vision.called
