import logging
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.services.providers.base import BaseProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.xai_provider import XAIProvider
from app.services.providers.huggingface_provider import HuggingFaceProvider

logger = logging.getLogger(__name__)

class AIRouter:
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "xai": XAIProvider(),
            "huggingface": HuggingFaceProvider(),
        }

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        return self.providers.get(name.lower().strip())

    def get_ordered_providers(self, capability: str = "text") -> List[BaseProvider]:
        """
        Returns list of configured providers matching the requested capability,
        ordered by settings.priority_list.
        """
        ordered = []
        priority_keys = settings.priority_list

        # Add providers in priority order
        for key in priority_keys:
            p = self.get_provider(key)
            if p and p.is_configured:
                if capability == "vision" and not p.supports_vision:
                    continue
                ordered.append(p)

        # Append any other configured providers not in priority list
        for key, p in self.providers.items():
            if key not in priority_keys and p.is_configured:
                if capability == "vision" and not p.supports_vision:
                    continue
                ordered.append(p)

        return ordered

    async def route_text_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Executes text generation with intelligent provider fallback.
        Returns (response_text, provider_name_used).
        """
        eligible = self.get_ordered_providers(capability="text")
        if not eligible:
            return (
                "⚠️ **No AI Provider Configured**\n\n"
                "Please configure at least one provider in `backend/.env`:\n"
                "- `OPENAI_API_KEY` (OpenAI)\n"
                "- `GEMINI_API_KEY` (Google Gemini)\n"
                "- `XAI_API_KEY` (xAI Grok)\n"
                "- `HF_TOKEN` (Hugging Face)\n\n"
                "Restart the server after updating `.env`.",
                "none"
            )

        attempt_errors = []

        for provider in eligible:
            logger.info(f"Attempting text generation with provider: {provider.name} (model: {provider.model_name})")
            try:
                result = await provider.generate_text(
                    messages=messages,
                    system_prompt=system_prompt,
                    context_str=context_str
                )
                if result:
                    logger.info(f"Provider {provider.name} succeeded.")
                    return result, provider.name
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Provider {provider.name} failed: {err_msg}")
                attempt_errors.append(f"{provider.name}: {err_msg}")
                # Fallback directly to next eligible provider

        # All eligible providers failed
        composite_error = (
            "⚠️ **All Configured AI Providers Failed**\n\n"
            "Summary of provider attempts:\n"
            + "\n".join(f"- **{err}**" for err in attempt_errors)
            + "\n\nPlease check your API keys, quotas, or network connectivity."
        )
        return composite_error, "failed"

    async def route_vision(
        self,
        image_path: str,
        prompt: str
    ) -> Tuple[str, str]:
        """
        Executes image understanding with intelligent vision-capable fallback.
        Returns (response_text, provider_name_used).
        """
        eligible = self.get_ordered_providers(capability="vision")
        if not eligible:
            return (
                "⚠️ **No Vision-Capable Provider Configured**\n\n"
                "Image understanding requires a vision-capable provider. Please configure one of:\n"
                "- `GEMINI_API_KEY` (Gemini 1.5/2.0 Flash)\n"
                "- `OPENAI_API_KEY` (GPT-4o / GPT-4o-mini)\n"
                "- `XAI_API_KEY` (Grok 2 Vision)\n\n"
                "Then restart the server.",
                "none"
            )

        attempt_errors = []

        for provider in eligible:
            logger.info(f"Attempting vision analysis with provider: {provider.name} (model: {provider.model_name})")
            try:
                result = await provider.generate_vision(
                    image_path=image_path,
                    prompt=prompt
                )
                if result:
                    logger.info(f"Provider {provider.name} vision succeeded.")
                    return result, provider.name
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Provider {provider.name} vision failed: {err_msg}")
                attempt_errors.append(f"{provider.name}: {err_msg}")

        composite_error = (
            "⚠️ **Vision Analysis Failed Across All Compatible Providers**\n\n"
            + "\n".join(f"- **{err}**" for err in attempt_errors)
        )
        return composite_error, "failed"

    async def get_diagnostics(self) -> List[Dict[str, Any]]:
        """
        Returns safe diagnostics for all four providers without exposing secrets.
        """
        results = []
        for name, provider in self.providers.items():
            diag = {
                "name": name,
                "model": provider.model_name,
                "configured": provider.is_configured,
                "supports_vision": provider.supports_vision,
                "status": "ready" if provider.is_configured else "missing_key",
                "verified": False,
                "error": None
            }
            if provider.is_configured:
                test_res = await provider.test_connection()
                diag["verified"] = test_res.get("verified", False)
                diag["error"] = test_res.get("error")
                if not diag["verified"]:
                    diag["status"] = "error"
            results.append(diag)
        return results

ai_router = AIRouter()
