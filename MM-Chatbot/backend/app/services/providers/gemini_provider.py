import asyncio
import logging
from typing import List, Dict, Any, Optional
from PIL import Image
import google.generativeai as genai
from app.config import settings
from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseProvider):
    name: str = "gemini"
    supports_vision: bool = True

    @property
    def is_configured(self) -> bool:
        key = settings.GEMINI_API_KEY.strip()
        return bool(key and not key.startswith("PASTE_") and key != "your_gemini_api_key_here")

    @property
    def model_name(self) -> str:
        return settings.GEMINI_MODEL or "gemini-3.5-flash-lite"

    def _configure(self):
        genai.configure(api_key=settings.GEMINI_API_KEY.strip(), transport="rest")

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> str:
        self._configure()
        full_system = system_prompt or "You are a helpful, accurate multimodal personal AI assistant."
        if context_str:
            full_system += f"\n\n{context_str}"

        def _call_text():
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=full_system
            )
            gemini_history = []
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})

            chat = model.start_chat(history=gemini_history)
            latest_user_message = messages[-1]["content"] if messages else ""
            response = chat.send_message(latest_user_message)
            return response.text.strip()

        return await asyncio.to_thread(_call_text)

    async def generate_vision(
        self,
        image_path: str,
        prompt: str
    ) -> str:
        self._configure()
        user_prompt = prompt.strip() or "Describe what you see in this image in detail. If identifying a location, explicitly state uncertainty if not positive."

        def _call_vision():
            img = Image.open(image_path)
            model = genai.GenerativeModel(model_name=self.model_name)
            response = model.generate_content([user_prompt, img])
            return response.text.strip()

        return await asyncio.to_thread(_call_vision)

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"configured": False, "verified": False, "error": "API key not configured"}
        try:
            self._configure()
            # Lightweight check: retrieve model metadata without generation
            model_id = self.model_name if self.model_name.startswith("models/") else f"models/{self.model_name}"
            genai.get_model(model_id)
            return {"configured": True, "verified": True, "model": self.model_name, "error": None}
        except Exception as e:
            logger.warning(f"Gemini test_connection error: {e}")
            return {"configured": True, "verified": False, "model": self.model_name, "error": str(e)}
