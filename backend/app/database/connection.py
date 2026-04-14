"""
Database connection management for SQLite and ChromaDB.
Provides session management and database initialization.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import settings
from .models import Base


# SQLite async engine
async_engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.debug,
    connect_args={"check_same_thread": False}
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# ChromaDB client
def get_chroma_client() -> chromadb.Client:
    """Get ChromaDB client with persistent storage."""
    # Ensure ChromaDB directory exists
    os.makedirs(settings.chromadb_path, exist_ok=True)

    client = chromadb.Client(
        ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=settings.chromadb_path,
            anonymized_telemetry=False
        )
    )
    return client


# Global ChromaDB client instance
chroma_client = None


def get_chroma() -> chromadb.Client:
    """Get or create global ChromaDB client."""
    global chroma_client
    if chroma_client is None:
        chroma_client = get_chroma_client()
    return chroma_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()


def init_chroma_collections() -> None:
    """Initialize ChromaDB collections for embeddings."""
    client = get_chroma()

    # Collection for document chunks
    try:
        client.get_collection("document_chunks")
    except Exception:
        client.create_collection(
            name="document_chunks",
            metadata={"description": "Document text chunks with embeddings"}
        )

    # Collection for entities
    try:
        client.get_collection("entities")
    except Exception:
        client.create_collection(
            name="entities",
            metadata={"description": "Entity embeddings for similarity search"}
        )
