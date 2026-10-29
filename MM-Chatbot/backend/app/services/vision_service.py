import os
import logging
from typing import Optional, Tuple
from app.config import settings
from app.services.ai_router import ai_router

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

class VisionService:
    @staticmethod
    def is_valid_image(filename: str, file_size: int) -> bool:
        """Validates image extension and size limit (10MB)."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return False
        if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            return False
        return True

    @staticmethod
    async def analyze_image(image_path: str, user_prompt: str) -> str:
        """
        Analyzes image using vision-capable providers through AIRouter with fallback.
        """
        reply, _ = await ai_router.route_vision(image_path, user_prompt)
        return reply

    @staticmethod
    async def analyze_image_with_meta(image_path: str, user_prompt: str) -> Tuple[str, str]:
        """
        Returns (reply, provider_used).
        """
        return await ai_router.route_vision(image_path, user_prompt)
