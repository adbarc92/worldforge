"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env files.
"""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # LLM Provider Configuration
    llm_provider: Literal["claude", "ollama"] = Field(
        default="claude",
        description="LLM provider to use"
    )

    # Claude API Configuration
    claude_api_key: str = Field(default="", description="Claude API key")
    claude_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude model to use"
    )
    claude_max_tokens: int = Field(default=4096, description="Max tokens for Claude")
    claude_temperature: float = Field(default=0.0, description="Claude temperature")

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://ollama:11434",
        description="Ollama base URL"
    )
    ollama_model: str = Field(
        default="mistral:7b-instruct",
        description="Ollama model to use"
    )
    ollama_temperature: float = Field(default=0.0, description="Ollama temperature")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:////data/worldforge.db",
        description="SQLite database URL"
    )
    chromadb_path: str = Field(
        default="/data/chromadb",
        description="ChromaDB persistence directory"
    )

    # Embeddings Configuration
    embeddings_model: str = Field(
        default="BAAI/bge-large-en-v1.5",
        description="Sentence transformer model for embeddings"
    )
    embeddings_device: str = Field(
        default="cpu",
        description="Device for embeddings (cpu or cuda)"
    )

    # Application Settings
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="production", description="Environment name")

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="FastAPI host")
    api_port: int = Field(default=8000, description="FastAPI port")

    # Frontend Settings
    streamlit_host: str = Field(default="0.0.0.0", description="Streamlit host")
    streamlit_port: int = Field(default=8501, description="Streamlit port")

    # File Storage
    documents_path: str = Field(
        default="/data/documents",
        description="Document storage path"
    )
    exports_path: str = Field(
        default="/data/exports",
        description="Exports storage path"
    )

    # Chunking Configuration
    chunk_size: int = Field(
        default=500,
        description="Text chunk size in tokens"
    )
    chunk_overlap: int = Field(
        default=50,
        description="Overlap between chunks in tokens"
    )

    # Similarity Thresholds
    similarity_threshold: float = Field(
        default=0.85,
        description="Similarity threshold for conflict detection"
    )
    high_confidence_threshold: float = Field(
        default=0.90,
        description="High confidence threshold for auto-approval"
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ("production", "prod")


# Global settings instance
settings = Settings()
