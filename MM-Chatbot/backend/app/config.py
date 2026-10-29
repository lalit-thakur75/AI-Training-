import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import dotenv_values

# Discover and merge .env files safely: backend/.env then root .env
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(_backend_dir)

_backend_env_path = os.path.join(_backend_dir, ".env")
_root_env_path = os.path.join(_root_dir, ".env")

# Pre-load dotenv values to ensure non-empty values take precedence
_merged_env: Dict[str, str] = {}
if os.path.exists(_root_env_path):
    _merged_env.update({k: v for k, v in dotenv_values(_root_env_path).items() if v})
if os.path.exists(_backend_env_path):
    _merged_env.update({k: v for k, v in dotenv_values(_backend_env_path).items() if v})

# Apply merged values to os.environ if not already present or if empty
for k, v in _merged_env.items():
    if v and (k not in os.environ or not os.environ[k]):
        os.environ[k] = v

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "Multimodal AI Personal Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    
    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"
    FALLBACK_SQLITE_URL: str = "sqlite+aiosqlite:///./data.db"
    
    # -------------------------------------------------------------
    # Four AI Providers Configuration
    # -------------------------------------------------------------
    # 1. OpenAI
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    
    # 2. Google Gemini
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite")
    
    # 3. Hugging Face
    HF_TOKEN: str = Field(default="")
    HF_MODEL: str = Field(default="meta-llama/Llama-3.1-8B-Instruct")
    
    # 4. Grok by xAI
    XAI_API_KEY: str = Field(default="")
    XAI_MODEL: str = Field(default="qwen/qwen3.8-27b")
    
    # Provider routing priority (comma-separated: openai, gemini, xai, huggingface)
    PROVIDER_PRIORITY: str = Field(default="xai,gemini,huggingface,openai")
    
    # Fallback / Legacy settings
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    
    # Embeddings & RAG
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIM: int = 3072
    RAG_SIMILARITY_THRESHOLD: float = 0.70
    RAG_TOP_K: int = 4
    
    # Web Search
    SEARCH_PROVIDER: str = "tavily"
    TAVILY_API_KEY: str = ""
    
    # Speech Services
    TTS_PROVIDER: str = "edge-tts"
    TTS_VOICE: str = "en-US-JennyNeural"
    STT_PROVIDER: str = "gemini"
    
    # Storage & Security
    UPLOAD_DIR: str = os.path.join(_backend_dir, "uploads")
    MAX_UPLOAD_SIZE_MB: int = 15
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=(_backend_env_path, _root_env_path),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def priority_list(self) -> List[str]:
        return [p.strip().lower() for p in self.PROVIDER_PRIORITY.split(",") if p.strip()]

settings = Settings()

# Backwards compatibility sync
if not settings.GEMINI_MODEL and settings.LLM_MODEL:
    settings.GEMINI_MODEL = settings.LLM_MODEL
