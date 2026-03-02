"""
Application configuration using Pydantic settings
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Canon Builder"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True)

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Security
    JWT_SECRET: str = Field(default="your_jwt_secret_here", env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database URLs
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="canon_builder_pass_2024", env="NEO4J_PASSWORD")
    POSTGRES_URL: str = Field(
        default="postgresql://canon:canon_pass@localhost:5432/canon_metadata",
        env="POSTGRES_URL"
    )

    # AI Services
    OLLAMA_URL: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    UNSTRUCTURED_URL: str = Field(default="http://localhost:8000", env="UNSTRUCTURED_URL")

    # LLM Configuration
    LLM_MODEL: str = "llama3.1:70b"
    EMBEDDING_MODEL: str = "bge-large-en-v1.5"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # RAG Configuration
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 10
    CONTEXT_MIN_TOKENS: int = 500
    CONTEXT_MAX_TOKENS: int = 2000

    # Graph Configuration
    GRAPH_TRAVERSAL_DEPTH: int = 2

    # Storage Paths
    DOCUMENTS_PATH: str = "/documents"
    DATA_PATH: str = "/data"

    # Cloud API Keys (optional fallback)
    OPENAI_API_KEY: str | None = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = Field(default=None, env="ANTHROPIC_API_KEY")

    # Monitoring (optional)
    SENTRY_DSN: str | None = Field(default=None, env="SENTRY_DSN")
    ENABLE_METRICS: bool = Field(default=False)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
