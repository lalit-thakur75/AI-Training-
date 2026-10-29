import logging
from typing import List, Dict, Any, Optional, Tuple
from app.services.ai_router import ai_router

logger = logging.getLogger(__name__)

class LLMService:
    @staticmethod
    async def generate_response(
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> str:
        """
        Delegates text generation to the multi-provider AIRouter with fallback.
        """
        text, _ = await ai_router.route_text_chat(
            messages=messages,
            system_prompt=system_prompt,
            context_str=context_str
        )
        return text

    @staticmethod
    async def generate_response_with_meta(
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Returns (response_text, provider_name_used).
        """
        return await ai_router.route_text_chat(
            messages=messages,
            system_prompt=system_prompt,
            context_str=context_str
        )
