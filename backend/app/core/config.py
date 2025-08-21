from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # LLM
    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-4o-mini"

    # Vector DB
    VECTOR_DB: str = "faiss"  # or "pinecone"

    # Pinecone (optional)
    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX: str | None = None
    PINECONE_CLOUD: str | None = None
    PINECONE_REGION: str | None = None

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        # Load .env from the repo root: backend/app/core/config.py -> up three levels
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")

settings = Settings()  # type: ignore

def cors_origins_list() -> List[str]:
    return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
