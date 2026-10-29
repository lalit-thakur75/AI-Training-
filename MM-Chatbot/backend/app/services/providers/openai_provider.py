import os
import base64
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    name: str = "openai"

    @property
    def is_configured(self) -> bool:
        key = settings.OPENAI_API_KEY.strip()
        return bool(key and not key.startswith("PASTE_") and key != "your_openai_api_key_here")

    @property
    def model_name(self) -> str:
        return settings.OPENAI_MODEL or "gpt-4o-mini"

    @property
    def supports_vision(self) -> bool:
        # gpt-4o, gpt-4o-mini, gpt-4-turbo support vision natively
        model = self.model_name.lower()
        return any(v in model for v in ["gpt-4o", "vision", "gpt-4-turbo"])

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY.strip(), timeout=30.0)

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> str:
        client = self._get_client()
        formatted_messages = []

        # System prompt + Sandboxed Context
        sys_content = system_prompt or "You are a helpful, practical multimodal personal AI assistant."
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
        user_prompt = prompt.strip() or "Describe this image in detail. If asked about a location, state uncertainty if not positive."

        with open(image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"

        response = await client.chat.completions.create(
            model=self.model_name,
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
            # Lightweight check: retrieve model metadata without generation cost
            await client.models.retrieve(self.model_name)
            return {"configured": True, "verified": True, "model": self.model_name, "error": None}
        except Exception as e:
            logger.warning(f"OpenAI test_connection error: {e}")
            return {"configured": True, "verified": False, "model": self.model_name, "error": str(e)}
