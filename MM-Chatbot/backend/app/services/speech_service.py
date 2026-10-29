import os
import io
import base64
import logging
from typing import Optional
import edge_tts
from app.config import settings

logger = logging.getLogger(__name__)

class SpeechService:
    @staticmethod
    async def text_to_speech(text: str, voice: Optional[str] = None) -> Optional[str]:
        """
        Converts text to speech audio using edge-tts (free) or OpenAI TTS.
        Returns audio formatted as a base64 encoded MP3 string.
        """
        clean_text = text.replace("*", "").replace("#", "").strip()
        if not clean_text:
            return None

        # Truncate to reasonable length for TTS
        if len(clean_text) > 1000:
            clean_text = clean_text[:1000] + "..."

        target_voice = voice or settings.TTS_VOICE or "en-US-JennyNeural"

        if settings.TTS_PROVIDER == "edge-tts":
            try:
                communicate = edge_tts.Communicate(clean_text, target_voice)
                audio_stream = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_stream.write(chunk["data"])
                
                audio_bytes = audio_stream.getvalue()
                if audio_bytes:
                    return base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.error(f"edge-tts error: {e}")
                return None

        elif settings.TTS_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                response = await client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=clean_text
                )
                audio_bytes = response.content
                return base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.error(f"OpenAI TTS error: {e}")
                return None

        return None

    @staticmethod
    async def transcribe_audio(audio_path: str) -> str:
        """
        Transcribes speech audio into text using Gemini or OpenAI Whisper.
        """
        if settings.STT_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                # Upload audio file to Gemini File API
                uploaded_file = genai.upload_file(path=audio_path)
                model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                response = model.generate_content([
                    uploaded_file,
                    "Transcribe this speech accurately into text. Output only the transcription, nothing else."
                ])
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini audio transcription error: {e}")
                
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                with open(audio_path, "rb") as audio_file:
                    transcript = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                    return transcript.text.strip()
            except Exception as e:
                logger.error(f"OpenAI Whisper transcription error: {e}")

        return "Audio transcription could not be completed. Please configure a valid GEMINI_API_KEY or OPENAI_API_KEY in .env."
