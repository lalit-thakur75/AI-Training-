from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://username:password@localhost:5432/multimodal_chatbot"
    LLM_API_KEY: str = ""
    SEARCH_API_KEY: str = ""
    STT_API_KEY: str = ""
    TTS_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
