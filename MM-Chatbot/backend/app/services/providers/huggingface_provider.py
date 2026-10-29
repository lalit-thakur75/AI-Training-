import logging
from typing import List, Dict, Any, Optional
import httpx
from openai import AsyncOpenAI
from app.config import settings
from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class HuggingFaceProvider(BaseProvider):
    name: str = "huggingface"
    supports_vision: bool = False

    @property
    def is_configured(self) -> bool:
        token = settings.HF_TOKEN.strip()
        return bool(token and not token.startswith("PASTE_") and token != "your_huggingface_token_here")

    @property
    def model_name(self) -> str:
        return settings.HF_MODEL or "meta-llama/Llama-3.2-3B-Instruct"

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=settings.HF_TOKEN.strip(),
            base_url="https://router.huggingface.co/v1",
            timeout=45.0
        )

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> str:
        # First attempt: OpenAI-compatible router endpoint
        try:
            client = self._get_client()
            formatted_messages = []

            sys_content = system_prompt or "You are a helpful personal AI assistant."
            if context_str:
                sys_content += f"\n\n{context_str}"
            formatted_messages.append({"role": "system", "content": sys_content})

            for msg in messages:
                role = "assistant" if msg["role"] in ["assistant", "model"] else "user"
                formatted_messages.append({"role": role, "content": msg["content"]})

            response = await client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content.strip()
        except Exception as router_err:
            logger.warning(f"HF Router endpoint error ({router_err}), attempting direct API fallback...")
            
            # Fallback: direct serverless inference endpoint
            async with httpx.AsyncClient(timeout=45.0) as http_client:
                url = f"https://api-inference.huggingface.co/models/{self.model_name}"
                headers = {"Authorization": f"Bearer {settings.HF_TOKEN.strip()}"}
                latest_msg = messages[-1]["content"] if messages else ""
                payload = {
                    "inputs": latest_msg,
                    "parameters": {"max_new_tokens": 512, "temperature": 0.7}
                }
                resp = await http_client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0].get("generated_text", str(data[0]))
                    return str(data)
                else:
                    raise RuntimeError(f"Hugging Face HTTP {resp.status_code}: {resp.text}")

    async def generate_vision(
        self,
        image_path: str,
        prompt: str
    ) -> str:
        raise NotImplementedError("Hugging Face provider currently configured for text models.")

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"configured": False, "verified": False, "error": "HF_TOKEN not configured"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Lightweight check to whoami endpoint
                resp = await client.get(
                    "https://huggingface.co/api/whoami-v2",
                    headers={"Authorization": f"Bearer {settings.HF_TOKEN.strip()}"}
                )
                if resp.status_code == 200:
                    user_data = resp.json()
                    username = user_data.get("name", "authenticated")
                    return {"configured": True, "verified": True, "model": self.model_name, "user": username, "error": None}
                else:
                    return {"configured": True, "verified": False, "model": self.model_name, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"configured": True, "verified": False, "model": self.model_name, "error": str(e)}
