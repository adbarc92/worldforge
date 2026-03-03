from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Required — app refuses to start without these.
    # Empty defaults allow module import; runtime checks should verify non-empty values.
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://canon_user:canon_pass@localhost:5432/canon_builder"
    )

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"

    # LLM models
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS: int = 3072

    # RAG parameters
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 10
    CONTEXT_MAX_TOKENS: int = 4000

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
    UPLOAD_DIR: str = "/app/uploads"


settings = Settings()
