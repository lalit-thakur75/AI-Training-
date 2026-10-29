import os
import base64
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class XAIProvider(BaseProvider):
    name: str = "xai"

    @property
    def is_configured(self) -> bool:
        key = settings.XAI_API_KEY.strip()
        return bool(key and not key.startswith("PASTE_") and key != "your_grok_key_here")

    @property
    def is_groq(self) -> bool:
        return settings.XAI_API_KEY.strip().startswith("gsk_")

    @property
    def base_url(self) -> str:
        if self.is_groq:
            return "https://api.groq.com/openai/v1"
        return "https://api.x.ai/v1"

    @property
    def model_name(self) -> str:
        if self.is_groq:
            # Groq model
            model = settings.XAI_MODEL
            if not model or "grok" in model.lower() or "llama-3.3" in model.lower():
                return "qwen/qwen3.8-27b"
            return model
        return settings.XAI_MODEL or "grok-2-vision-1212"

    @property
    def vision_model_name(self) -> str:
        if self.is_groq:
            return "llama-3.2-11b-vision-preview"
        return "grok-2-vision-1212"

    @property
    def supports_vision(self) -> bool:
        if self.is_groq:
            return False
        return "vision" in self.model_name.lower()

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=settings.XAI_API_KEY.strip(),
            base_url=self.base_url,
            timeout=30.0
        )

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> str:
        client = self._get_client()
        formatted_messages = []

        sys_content = system_prompt or "You are an intelligent, helpful personal AI assistant."
        if context_str:
            sys_content += f"\n\n{context_str}"
        formatted_messages.append({"role": "system", "content": sys_content})

        for msg in messages:
            role = "assistant" if msg["role"] in ["assistant", "model"] else "user"
            formatted_messages.append({"role": role, "content": msg["content"]})

        response = await client.chat.completions.create(
            model=self.model_name,
            messages=formatted_messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    async def generate_vision(
        self,
        image_path: str,
        prompt: str
    ) -> str:
        client = self._get_client()
        user_prompt = prompt.strip() or "Describe this image in detail. State uncertainty if a location cannot be identified definitively."

        with open(image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"

        target_model = self.vision_model_name if self.is_groq else self.model_name

        response = await client.chat.completions.create(
            model=target_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}
                        }
                    ]
                }
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"configured": False, "verified": False, "error": "API key not configured"}
        try:
            client = self._get_client()
            await client.models.list()
            provider_type = "Groq" if self.is_groq else "xAI"
            return {"configured": True, "verified": True, "type": provider_type, "model": self.model_name, "error": None}
        except Exception as e:
            logger.warning(f"XAI/Groq test_connection error: {e}")
            return {"configured": True, "verified": False, "model": self.model_name, "error": str(e)}
