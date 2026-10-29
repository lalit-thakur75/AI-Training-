import os
import uuid
import logging
import httpx
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class ImageGenService:
    @staticmethod
    async def generate_image(prompt: str) -> Dict[str, Any]:
        """
        Generates an image from prompt using OpenAI (dall-e-3 / dall-e-2) or Hugging Face.
        Saves image locally to UPLOAD_DIR and returns public URL and description.
        """
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Image generation prompt cannot be empty.")

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        filename = f"gen_{uuid.uuid4()}.png"
        local_path = os.path.join(settings.UPLOAD_DIR, filename)

        # 1. Attempt OpenAI DALL-E if configured
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("PASTE_"):
            try:
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.strip(), timeout=10.0)
                # Try dall-e-3, fallback to dall-e-2
                try:
                    res = await client.images.generate(
                        model="dall-e-3",
                        prompt=clean_prompt,
                        n=1,
                        size="1024x1024"
                    )
                except Exception as de3_err:
                    logger.warning(f"dall-e-3 failed ({de3_err}), trying dall-e-2...")
                    res = await client.images.generate(
                        model="dall-e-2",
                        prompt=clean_prompt,
                        n=1,
                        size="512x512"
                    )

                image_url = res.data[0].url
                revised_prompt = getattr(res.data[0], "revised_prompt", clean_prompt)

                # Download image to serve locally as well
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    img_resp = await http_client.get(image_url)
                    if img_resp.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(img_resp.content)

                return {
                    "image_url": f"http://localhost:8000/uploads/{filename}",
                    "remote_url": image_url,
                    "prompt": clean_prompt,
                    "revised_prompt": revised_prompt,
                    "provider": "openai-dalle",
                    "filename": filename
                }
            except Exception as e:
                logger.warning(f"OpenAI image generation error: {e}")

        # 2. Fallback to Hugging Face FLUX / SDXL if configured
        if settings.HF_TOKEN and not settings.HF_TOKEN.startswith("PASTE_"):
            try:
                hf_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
                headers = {"Authorization": f"Bearer {settings.HF_TOKEN.strip()}"}
                async with httpx.AsyncClient(timeout=60.0) as http_client:
                    resp = await http_client.post(hf_url, headers=headers, json={"inputs": clean_prompt})
                    if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                        with open(local_path, "wb") as f:
                            f.write(resp.content)
                        return {
                            "image_url": f"http://localhost:8000/uploads/{filename}",
                            "prompt": clean_prompt,
                            "provider": "huggingface-flux",
                            "filename": filename
                        }
            except Exception as hf_err:
                logger.warning(f"Hugging Face image gen error: {hf_err}")

        # 3. Reliable Fallback: Pollinations AI (High quality, zero quota block)
        try:
            import urllib.parse
            encoded = urllib.parse.quote(clean_prompt)
            poll_url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true"
            async with httpx.AsyncClient(timeout=45.0) as http_client:
                resp = await http_client.get(poll_url)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(local_path, "wb") as f:
                        f.write(resp.content)
                    return {
                        "image_url": f"http://localhost:8000/uploads/{filename}",
                        "remote_url": poll_url,
                        "prompt": clean_prompt,
                        "provider": "pollinations-ai",
                        "filename": filename
                    }
        except Exception as poll_err:
            logger.warning(f"Pollinations image generation fallback failed: {poll_err}")

        raise RuntimeError("No image generation provider succeeded. Ensure valid API keys or internet connection.")
