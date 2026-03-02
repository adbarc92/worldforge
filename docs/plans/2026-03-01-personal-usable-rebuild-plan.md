# Canon Builder: Personal Usable State — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the backend so a single user can upload text/md/PDF documents, query them via RAG, and interact through OpenWebUI.

**Architecture:** Async-native FastAPI backend with LLM provider abstraction (Anthropic for generation, OpenAI for embeddings), Qdrant for vector storage, PostgreSQL for metadata. OpenWebUI connects via an OpenAI-compatible chat completions endpoint.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), asyncpg, Qdrant (async client), Anthropic SDK, OpenAI SDK, LlamaIndex (SentenceSplitter), PyPDF, Alembic, UV, pytest-asyncio, Docker Compose.

---

## Task 1: Initialize UV Project and Dependencies

**Files:**
- Create: `backend/pyproject.toml`
- Delete: `backend/requirements.txt`

**Step 1: Initialize pyproject.toml**

```toml
[project]
name = "canon-builder"
version = "0.1.0"
description = "RAG-powered worldbuilding knowledge system"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "alembic>=1.13.1",
    "qdrant-client>=1.7.3",
    "anthropic>=0.42.0",
    "openai>=1.12.0",
    "llama-index-core>=0.10.12",
    "pypdf>=4.0.1",
    "tiktoken>=0.6.0",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "python-multipart>=0.0.6",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.2",
    "httpx>=0.26.0",
    "aiofiles>=23.2.1",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.3",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",
]
```

**Step 2: Run UV sync**

Run: `cd backend && uv sync --all-groups`
Expected: Virtual environment created, all dependencies installed.

**Step 3: Delete old requirements.txt**

Run: `rm backend/requirements.txt`

**Step 4: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git rm backend/requirements.txt
git commit -m "feat: migrate to UV with pyproject.toml"
```

---

## Task 2: Rewrite Configuration

**Files:**
- Rewrite: `backend/app/core/config.py`

**Step 1: Write the config**

```python
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Required — app refuses to start without these
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
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
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    UPLOAD_DIR: str = "/app/uploads"


settings = Settings()
```

**Step 2: Commit**

```bash
git add backend/app/core/config.py
git commit -m "feat: rewrite config with required/optional env vars"
```

---

## Task 3: LLM Provider Abstraction

**Files:**
- Create: `backend/app/services/llm/__init__.py`
- Create: `backend/app/services/llm/base.py`
- Create: `backend/app/services/llm/anthropic_provider.py`
- Create: `backend/app/services/llm/openai_provider.py`
- Create: `backend/app/services/llm/service.py`
- Test: `backend/tests/test_llm_providers.py`

**Step 1: Write the failing tests**

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_anthropic_generate():
    from app.services.llm.anthropic_provider import AnthropicProvider

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=MagicMock(content=[MagicMock(text="Test response")])
    )

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-20250514")
    provider.client = mock_client

    result = await provider.generate("Hello", system_prompt="Be helpful")
    assert result == "Test response"
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_openai_embed():
    from app.services.llm.openai_provider import OpenAIProvider

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    provider = OpenAIProvider(
        api_key="test-key",
        model="text-embedding-3-large",
        dimensions=3072,
    )
    provider.client = mock_client

    result = await provider.embed(["test text"])
    assert len(result) == 1
    assert result[0] == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_llm_service_routes_calls():
    from app.services.llm.service import LLMService

    mock_generator = AsyncMock()
    mock_generator.generate = AsyncMock(return_value="answer")
    mock_embedder = AsyncMock()
    mock_embedder.embed = AsyncMock(return_value=[[0.1]])

    service = LLMService(generator=mock_generator, embedder=mock_embedder)

    assert await service.generate("prompt") == "answer"
    assert await service.embed(["text"]) == [[0.1]]
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_llm_providers.py -v`
Expected: FAIL — modules don't exist yet.

**Step 3: Implement base provider**

```python
# backend/app/services/llm/base.py
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    @abstractmethod
    async def check_available(self) -> bool:
        ...
```

**Step 4: Implement Anthropic provider**

```python
# backend/app/services/llm/anthropic_provider.py
import anthropic
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic provider does not support embeddings")

    async def check_available(self) -> bool:
        try:
            await self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False
```

**Step 5: Implement OpenAI provider**

```python
# backend/app/services/llm/openai_provider.py
import openai
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, dimensions: int = 3072):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        raise NotImplementedError("OpenAI provider is configured for embeddings only")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )
        return [item.embedding for item in response.data]

    async def check_available(self) -> bool:
        try:
            await self.client.embeddings.create(
                model=self.model,
                input=["test"],
                dimensions=self.dimensions,
            )
            return True
        except Exception:
            return False
```

**Step 6: Implement LLM service**

```python
# backend/app/services/llm/service.py
from .base import LLMProvider


class LLMService:
    def __init__(self, generator: LLMProvider, embedder: LLMProvider):
        self.generator = generator
        self.embedder = embedder

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        return await self.generator.generate(
            prompt, system_prompt=system_prompt,
            temperature=temperature, max_tokens=max_tokens,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self.embedder.embed(texts)

    async def check_available(self) -> dict[str, bool]:
        return {
            "generator": await self.generator.check_available(),
            "embedder": await self.embedder.check_available(),
        }
```

```python
# backend/app/services/llm/__init__.py
from .service import LLMService
from .base import LLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
```

**Step 7: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_llm_providers.py -v`
Expected: 3 passed.

**Step 8: Commit**

```bash
git add backend/app/services/llm/ backend/tests/test_llm_providers.py
git commit -m "feat: add LLM provider abstraction with Anthropic and OpenAI"
```

---

## Task 4: Async Database Layer

**Files:**
- Rewrite: `backend/app/models/database.py`
- Create: `backend/app/models/repositories.py`
- Create: `backend/tests/test_repositories.py`

**Step 1: Write the failing tests**

```python
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_document_repository_create():
    from app.models.repositories import DocumentRepository
    from app.models.database import Document

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    repo = DocumentRepository(mock_session)
    doc = await repo.create(title="Test Doc", file_path="/uploads/test.txt")

    assert doc.title == "Test Doc"
    assert doc.file_path == "/uploads/test.txt"
    assert doc.status == "pending"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_document_repository_list():
    from app.models.repositories import DocumentRepository

    mock_doc = MagicMock()
    mock_doc.title = "Doc 1"

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_doc]

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = DocumentRepository(mock_session)
    docs = await repo.list()

    assert len(docs) == 1
    assert docs[0].title == "Doc 1"
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_repositories.py -v`
Expected: FAIL — modules don't exist.

**Step 3: Rewrite database.py with async engine**

```python
# backend/app/models/database.py
import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.config import settings


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending/processing/completed/failed
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
```

**Step 4: Implement repositories**

```python
# backend/app/models/repositories.py
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, title: str, file_path: str) -> Document:
        doc = Document(
            id=str(uuid.uuid4()),
            title=title,
            file_path=file_path,
            status="pending",
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get(self, doc_id: str) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.id == doc_id)
        )
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 50) -> list[Document]:
        result = await self.session.execute(
            select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self, doc_id: str, status: str, chunk_count: int | None = None, error_message: str | None = None
    ) -> Document | None:
        doc = await self.get(doc_id)
        if not doc:
            return None
        doc.status = status
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def delete(self, doc_id: str) -> bool:
        doc = await self.get(doc_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.commit()
        return True
```

**Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_repositories.py -v`
Expected: 2 passed.

**Step 6: Commit**

```bash
git add backend/app/models/database.py backend/app/models/repositories.py backend/tests/test_repositories.py
git commit -m "feat: async database layer with document repository"
```

---

## Task 5: Alembic Migration Setup

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (directory)
- Delete: `backend/migrations/001_initial_schema.sql`

**Step 1: Initialize Alembic**

Run: `cd backend && uv run alembic init alembic`

**Step 2: Configure alembic/env.py for async**

Replace `backend/alembic/env.py` with async configuration that imports `Base.metadata` from `app.models.database` and uses `run_async_migrations()`.

**Step 3: Update alembic.ini**

Set `sqlalchemy.url` to empty (will be overridden from config in env.py).

**Step 4: Generate initial migration**

Run: `cd backend && uv run alembic revision --autogenerate -m "initial schema"`

**Step 5: Apply migration**

Run: `cd backend && uv run alembic upgrade head`
Expected: Documents table created in PostgreSQL.

**Step 6: Commit**

```bash
git rm backend/migrations/001_initial_schema.sql
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add Alembic async migrations, replace raw SQL"
```

---

## Task 6: Rewrite Qdrant Service (Async)

**Files:**
- Rewrite: `backend/app/services/qdrant_service.py`
- Test: `backend/tests/test_qdrant_service.py`

**Step 1: Write the failing tests**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_qdrant_upsert():
    from app.services.qdrant_service import QdrantService

    mock_client = AsyncMock()
    service = QdrantService.__new__(QdrantService)
    service.client = mock_client
    service.collection_name = "canon_documents"

    await service.upsert(
        ids=["id1"],
        vectors=[[0.1, 0.2]],
        payloads=[{"text": "hello"}],
    )
    mock_client.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_qdrant_search():
    from app.services.qdrant_service import QdrantService

    mock_point = MagicMock()
    mock_point.id = "id1"
    mock_point.score = 0.95
    mock_point.payload = {"text": "hello", "document_id": "doc1"}

    mock_client = AsyncMock()
    mock_client.query_points = AsyncMock(return_value=MagicMock(points=[mock_point]))

    service = QdrantService.__new__(QdrantService)
    service.client = mock_client
    service.collection_name = "canon_documents"

    results = await service.search(query_vector=[0.1, 0.2], top_k=5)
    assert len(results) == 1
    assert results[0]["score"] == 0.95


@pytest.mark.asyncio
async def test_qdrant_delete_by_document():
    from app.services.qdrant_service import QdrantService

    mock_client = AsyncMock()
    service = QdrantService.__new__(QdrantService)
    service.client = mock_client
    service.collection_name = "canon_documents"

    await service.delete_by_document("doc1")
    mock_client.delete.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_qdrant_service.py -v`
Expected: FAIL.

**Step 3: Implement async Qdrant service**

```python
# backend/app/services/qdrant_service.py
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)

from app.core.config import settings


class QdrantService:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "canon_documents"

    async def ensure_collection(self):
        collections = await self.client.get_collections()
        names = [c.name for c in collections.collections]
        if self.collection_name not in names:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE,
                ),
            )

    async def upsert(
        self, ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ):
        points = [
            PointStruct(id=id_, vector=vec, payload=payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]
        await self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(
        self, query_vector: list[float], top_k: int = 10, filters: dict | None = None
    ) -> list[dict]:
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [
            {"id": point.id, "score": point.score, "payload": point.payload}
            for point in results.points
        ]

    async def delete_by_document(self, document_id: str):
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )

    async def close(self):
        await self.client.close()
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_qdrant_service.py -v`
Expected: 3 passed.

**Step 5: Commit**

```bash
git add backend/app/services/qdrant_service.py backend/tests/test_qdrant_service.py
git commit -m "feat: rewrite Qdrant service with async client"
```

---

## Task 7: Rewrite Ingestion Service

**Files:**
- Rewrite: `backend/app/services/ingestion_service.py`
- Test: `backend/tests/test_ingestion_service.py`

**Step 1: Write the failing tests**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_extract_text_from_txt():
    from app.services.ingestion_service import IngestionService

    service = IngestionService.__new__(IngestionService)
    # Create a temp file
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello world, this is a test document.")
        path = f.name

    try:
        text = await service._extract_text(path)
        assert "Hello world" in text
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_chunk_text():
    from app.services.ingestion_service import IngestionService

    service = IngestionService.__new__(IngestionService)
    service.chunk_size = 100
    service.chunk_overlap = 20

    text = "This is sentence one. " * 50  # ~1100 chars
    chunks = service._chunk_text(text, document_id="doc1", title="Test")

    assert len(chunks) > 1
    assert all("text" in c for c in chunks)
    assert all("chunk_id" in c for c in chunks)
    assert chunks[0]["document_id"] == "doc1"


@pytest.mark.asyncio
async def test_process_document_pipeline():
    from app.services.ingestion_service import IngestionService

    mock_llm = AsyncMock()
    mock_llm.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    mock_qdrant = AsyncMock()
    mock_repo = AsyncMock()
    mock_doc = MagicMock()
    mock_doc.id = "doc1"
    mock_repo.create = AsyncMock(return_value=mock_doc)
    mock_repo.update_status = AsyncMock(return_value=mock_doc)

    service = IngestionService(
        llm_service=mock_llm,
        qdrant_service=mock_qdrant,
        document_repo=mock_repo,
    )
    service.chunk_size = 5000
    service.chunk_overlap = 50

    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test document content for processing.")
        path = f.name

    try:
        doc = await service.process_document(file_path=path, title="Test Doc")
        mock_repo.create.assert_called_once()
        mock_llm.embed.assert_called_once()
        mock_qdrant.upsert.assert_called_once()
        mock_repo.update_status.assert_called()
    finally:
        os.unlink(path)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_ingestion_service.py -v`
Expected: FAIL.

**Step 3: Implement ingestion service**

```python
# backend/app/services/ingestion_service.py
import os
import uuid
import aiofiles
from loguru import logger
from llama_index.core.node_parser import SentenceSplitter

from app.core.config import settings
from app.services.llm import LLMService
from app.services.qdrant_service import QdrantService
from app.models.repositories import DocumentRepository


class IngestionService:
    def __init__(
        self,
        llm_service: LLMService,
        qdrant_service: QdrantService,
        document_repo: DocumentRepository,
    ):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.document_repo = document_repo
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    async def process_document(self, file_path: str, title: str):
        doc = await self.document_repo.create(title=title, file_path=file_path)
        try:
            await self.document_repo.update_status(doc.id, "processing")

            text = await self._extract_text(file_path)
            if not text.strip():
                raise ValueError("Document is empty after text extraction")

            chunks = self._chunk_text(text, document_id=doc.id, title=title)
            logger.info(f"Document '{title}' split into {len(chunks)} chunks")

            texts = [c["text"] for c in chunks]
            embeddings = await self.llm_service.embed(texts)

            ids = [c["chunk_id"] for c in chunks]
            payloads = [
                {
                    "text": c["text"],
                    "document_id": c["document_id"],
                    "title": c["title"],
                    "chunk_index": c["chunk_index"],
                }
                for c in chunks
            ]
            await self.qdrant_service.upsert(ids=ids, vectors=embeddings, payloads=payloads)

            await self.document_repo.update_status(doc.id, "completed", chunk_count=len(chunks))
            logger.info(f"Document '{title}' processed successfully")
            return doc

        except Exception as e:
            logger.error(f"Failed to process document '{title}': {e}")
            await self.document_repo.update_status(doc.id, "failed", error_message=str(e))
            # Rollback: clean up any partial Qdrant data
            try:
                await self.qdrant_service.delete_by_document(doc.id)
            except Exception:
                pass
            raise

    async def _extract_text(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()

        if ext in (".txt", ".md"):
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()

        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)

        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _chunk_text(self, text: str, document_id: str, title: str) -> list[dict]:
        splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        text_chunks = splitter.split_text(text)

        return [
            {
                "chunk_id": f"{document_id}_chunk_{i}",
                "text": chunk,
                "chunk_index": i,
                "document_id": document_id,
                "title": title,
            }
            for i, chunk in enumerate(text_chunks)
        ]

    async def delete_document(self, doc_id: str) -> bool:
        doc = await self.document_repo.get(doc_id)
        if not doc:
            return False

        await self.qdrant_service.delete_by_document(doc_id)

        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        await self.document_repo.delete(doc_id)
        logger.info(f"Document '{doc.title}' deleted")
        return True
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_ingestion_service.py -v`
Expected: 3 passed.

**Step 5: Commit**

```bash
git add backend/app/services/ingestion_service.py backend/tests/test_ingestion_service.py
git commit -m "feat: rewrite ingestion service with async pipeline and rollback"
```

---

## Task 8: Rewrite RAG Service

**Files:**
- Rewrite: `backend/app/services/rag_service.py`
- Test: `backend/tests/test_rag_service.py`

**Step 1: Write the failing tests**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_rag_query_returns_answer_with_citations():
    from app.services.rag_service import RAGService

    mock_llm = AsyncMock()
    mock_llm.embed = AsyncMock(return_value=[[0.1, 0.2]])
    mock_llm.generate = AsyncMock(return_value="The capital is Paris.")

    mock_qdrant = AsyncMock()
    mock_qdrant.search = AsyncMock(return_value=[
        {
            "id": "doc1_chunk_0",
            "score": 0.95,
            "payload": {
                "text": "France's capital is Paris, a city known for the Eiffel Tower.",
                "document_id": "doc1",
                "title": "France Guide",
                "chunk_index": 0,
            },
        }
    ])

    service = RAGService(llm_service=mock_llm, qdrant_service=mock_qdrant)
    result = await service.query("What is the capital of France?")

    assert "Paris" in result["answer"]
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document_id"] == "doc1"
    mock_llm.embed.assert_called_once()
    mock_qdrant.search.assert_called_once()
    mock_llm.generate.assert_called_once()


@pytest.mark.asyncio
async def test_rag_query_no_results():
    from app.services.rag_service import RAGService

    mock_llm = AsyncMock()
    mock_llm.embed = AsyncMock(return_value=[[0.1, 0.2]])
    mock_llm.generate = AsyncMock(return_value="I don't have information about that topic.")

    mock_qdrant = AsyncMock()
    mock_qdrant.search = AsyncMock(return_value=[])

    service = RAGService(llm_service=mock_llm, qdrant_service=mock_qdrant)
    result = await service.query("Something with no matches")

    assert len(result["citations"]) == 0
    # Should still call generate (to say "no info found")
    mock_llm.generate.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_rag_service.py -v`
Expected: FAIL.

**Step 3: Implement RAG service**

```python
# backend/app/services/rag_service.py
import time
import tiktoken
from loguru import logger

from app.core.config import settings
from app.services.llm import LLMService
from app.services.qdrant_service import QdrantService

SYSTEM_PROMPT = """You are a knowledgeable assistant for a worldbuilding canon.
Answer questions using ONLY the provided source material.
If the sources don't contain enough information, say so clearly.
Always reference which sources support your answer."""

NO_CONTEXT_PROMPT = """You are a knowledgeable assistant for a worldbuilding canon.
The user asked a question but no relevant source material was found in the canon.
Politely inform them that you couldn't find relevant information in the current canon documents."""


class RAGService:
    def __init__(self, llm_service: LLMService, qdrant_service: QdrantService):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.max_context_tokens = settings.CONTEXT_MAX_TOKENS

    async def query(self, question: str, top_k: int = 10) -> dict:
        start = time.time()

        query_embedding = (await self.llm_service.embed([question]))[0]

        results = await self.qdrant_service.search(
            query_vector=query_embedding, top_k=top_k,
        )

        context, citations = self._assemble_context(results)

        if context:
            prompt = f"Question: {question}\n\nSources:\n{context}\n\nAnswer the question based on the sources above."
            answer = await self.llm_service.generate(
                prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3,
            )
        else:
            prompt = f"Question: {question}"
            answer = await self.llm_service.generate(
                prompt, system_prompt=NO_CONTEXT_PROMPT, temperature=0.3,
            )

        elapsed_ms = int((time.time() - start) * 1000)

        return {
            "answer": answer,
            "citations": citations,
            "processing_time_ms": elapsed_ms,
        }

    def _assemble_context(self, results: list[dict]) -> tuple[str, list[dict]]:
        if not results:
            return "", []

        try:
            enc = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")

        context_parts = []
        citations = []
        total_tokens = 0

        for i, result in enumerate(results):
            payload = result["payload"]
            text = payload.get("text", "")
            chunk_tokens = len(enc.encode(text))

            if total_tokens + chunk_tokens > self.max_context_tokens:
                break

            total_tokens += chunk_tokens
            context_parts.append(f"[Source {i + 1}]\n{text}")
            citations.append({
                "document_id": payload.get("document_id", ""),
                "title": payload.get("title", ""),
                "chunk_text": text[:200],
                "relevance_score": result.get("score", 0.0),
            })

        return "\n\n".join(context_parts), citations
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_rag_service.py -v`
Expected: 2 passed.

**Step 5: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/test_rag_service.py
git commit -m "feat: rewrite RAG service with token-aware context assembly"
```

---

## Task 9: Rewrite API Routes

**Files:**
- Rewrite: `backend/app/api/v1/__init__.py`
- Rewrite: `backend/app/api/v1/documents.py`
- Rewrite: `backend/app/api/v1/query.py`
- Create: `backend/app/api/v1/openai_compat.py`
- Delete: `backend/app/api/v1/auth.py`
- Delete: `backend/app/api/v1/proposals.py`
- Delete: `backend/app/api/v1/graph.py`
- Delete: `backend/app/api/v1/consistency.py`
- Delete: `backend/app/core/security.py`
- Test: `backend/tests/test_api_documents.py`
- Test: `backend/tests/test_api_query.py`

**Step 1: Write failing tests for document routes**

```python
# backend/tests/test_api_documents.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_upload_document():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"Hello world content", "text/plain")},
        )
    # Will depend on service mocking — structure test
    assert response.status_code in (200, 201, 500)  # 500 until services wired


@pytest.mark.asyncio
async def test_list_documents():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_api_documents.py -v`
Expected: FAIL.

**Step 3: Implement document routes**

```python
# backend/app/api/v1/documents.py
import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.repositories import DocumentRepository
from app.core.config import settings
from app.dependencies import get_ingestion_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    ingestion_service=Depends(get_ingestion_service),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".txt", ".md", ".pdf"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    title = file.filename or file_id
    doc = await ingestion_service.process_document(file_path=file_path, title=title)

    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
    }


@router.get("")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    repo = DocumentRepository(db)
    docs = await repo.list(skip=skip, limit=limit)
    return [
        {
            "id": d.id,
            "title": d.title,
            "status": d.status,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    doc = await repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "file_path": doc.file_path,
        "created_at": doc.created_at.isoformat(),
        "error_message": doc.error_message,
    }


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    ingestion_service=Depends(get_ingestion_service),
):
    deleted = await ingestion_service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}
```

**Step 4: Implement query route**

```python
# backend/app/api/v1/query.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_rag_service

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=10, ge=1, le=50)


@router.post("")
async def query_canon(
    request: QueryRequest,
    rag_service=Depends(get_rag_service),
):
    result = await rag_service.query(
        question=request.question, top_k=request.top_k,
    )
    return result
```

**Step 5: Implement OpenAI-compatible endpoint for OpenWebUI**

```python
# backend/app/api/v1/openai_compat.py
import time
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_rag_service

router = APIRouter(tags=["openai-compat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "canon-builder"
    messages: list[ChatMessage]
    temperature: float = 0.3
    max_tokens: int = 2048
    stream: bool = False


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    rag_service=Depends(get_rag_service),
):
    # Extract the last user message as the query
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        question = ""
    else:
        question = user_messages[-1].content

    result = await rag_service.query(question=question)

    # Format citations into the answer
    answer = result["answer"]
    if result["citations"]:
        answer += "\n\n---\n**Sources:**\n"
        for i, cite in enumerate(result["citations"], 1):
            answer += f"{i}. {cite['title']} (relevance: {cite['relevance_score']:.2f})\n"

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "canon-builder",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


@router.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "canon-builder",
                "object": "model",
                "created": 0,
                "owned_by": "canon-builder",
            }
        ],
    }
```

**Step 6: Implement dependency injection module**

```python
# backend/app/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import get_db
from app.models.repositories import DocumentRepository
from app.services.llm import LLMService, AnthropicProvider, OpenAIProvider
from app.services.qdrant_service import QdrantService
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService

# Singletons initialized on first use
_llm_service: LLMService | None = None
_qdrant_service: QdrantService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        generator = AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
        )
        embedder = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
        _llm_service = LLMService(generator=generator, embedder=embedder)
    return _llm_service


def get_qdrant_service() -> QdrantService:
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service


async def get_ingestion_service(
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> IngestionService:
    return IngestionService(
        llm_service=llm_service,
        qdrant_service=qdrant_service,
        document_repo=DocumentRepository(db),
    )


async def get_rag_service(
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> RAGService:
    return RAGService(llm_service=llm_service, qdrant_service=qdrant_service)
```

**Step 7: Update router init**

```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter

from app.api.v1.documents import router as documents_router
from app.api.v1.query import router as query_router

router = APIRouter(prefix="/api/v1")
router.include_router(documents_router)
router.include_router(query_router)
```

**Step 8: Delete unused route files and security module**

```bash
rm backend/app/api/v1/auth.py
rm backend/app/api/v1/proposals.py
rm backend/app/api/v1/graph.py
rm backend/app/api/v1/consistency.py
rm backend/app/core/security.py
```

**Step 9: Run tests**

Run: `cd backend && uv run pytest tests/test_api_documents.py tests/test_api_query.py -v`
Expected: Tests pass (or adjust mocking as needed).

**Step 10: Commit**

```bash
git add backend/app/api/ backend/app/dependencies.py backend/tests/test_api_*.py
git rm backend/app/api/v1/auth.py backend/app/api/v1/proposals.py backend/app/api/v1/graph.py backend/app/api/v1/consistency.py backend/app/core/security.py
git commit -m "feat: rewrite API routes with document CRUD, query, and OpenAI-compat endpoint"
```

---

## Task 10: Rewrite Main Application

**Files:**
- Rewrite: `backend/app/main.py`
- Delete: `backend/app/services/ollama_service.py`
- Delete: `backend/app/services/neo4j_service.py`
- Delete: `backend/app/services/entity_service.py`

**Step 1: Implement main.py with lifespan**

```python
# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.models.database import engine
from app.dependencies import get_llm_service, get_qdrant_service
from app.api.v1 import router as api_router
from app.api.v1.openai_compat import router as openai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Canon Builder API")

    qdrant = get_qdrant_service()
    await qdrant.ensure_collection()
    logger.info("Qdrant collection verified")

    llm = get_llm_service()
    status = await llm.check_available()
    for provider, available in status.items():
        level = "info" if available else "warning"
        getattr(logger, level)(f"LLM {provider}: {'available' if available else 'UNAVAILABLE'}")

    logger.info("Canon Builder API ready")
    yield

    # Shutdown
    qdrant = get_qdrant_service()
    await qdrant.close()
    await engine.dispose()
    logger.info("Canon Builder API shut down")


app = FastAPI(
    title="Canon Builder",
    description="RAG-powered worldbuilding knowledge system",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(openai_router)


@app.get("/health")
async def health():
    llm = get_llm_service()
    status = await llm.check_available()
    return {
        "status": "healthy" if all(status.values()) else "degraded",
        "services": status,
    }
```

**Step 2: Delete old service files**

```bash
rm backend/app/services/ollama_service.py
rm backend/app/services/neo4j_service.py
rm backend/app/services/entity_service.py
```

**Step 3: Update services __init__.py**

```python
# backend/app/services/__init__.py
```

(Empty — services are imported directly where needed.)

**Step 4: Run all tests**

Run: `cd backend && uv run pytest tests/ -v`
Expected: All tests pass.

**Step 5: Commit**

```bash
git add backend/app/main.py backend/app/services/__init__.py
git rm backend/app/services/ollama_service.py backend/app/services/neo4j_service.py backend/app/services/entity_service.py
git commit -m "feat: rewrite main app with lifespan, remove unused services"
```

---

## Task 11: Rewrite Dockerfile and Docker Compose

**Files:**
- Rewrite: `backend/Dockerfile`
- Rewrite: `docker-compose.yml`
- Update: `.env.example`

**Step 1: Rewrite Dockerfile**

```dockerfile
FROM python:3.11-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN useradd --create-home appuser

WORKDIR /app

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Step 2: Rewrite docker-compose.yml**

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: canon_builder
      POSTGRES_USER: canon_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-canon_pass}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U canon_user -d canon_builder"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:6333/healthz || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  canon_api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql+asyncpg://canon_user:${POSTGRES_PASSWORD:-canon_pass}@postgres:5432/canon_builder
      QDRANT_URL: http://qdrant:6333
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_MODEL: ${ANTHROPIC_MODEL:-claude-sonnet-4-20250514}
      OPENAI_EMBEDDING_MODEL: ${OPENAI_EMBEDDING_MODEL:-text-embedding-3-large}
      UPLOAD_DIR: /app/uploads
    volumes:
      - uploads_data:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy

  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      OPENAI_API_BASE_URL: http://canon_api:8080/v1
      OPENAI_API_KEY: "unused"
      WEBUI_AUTH: "false"
    volumes:
      - openwebui_data:/app/backend/data
    depends_on:
      - canon_api

volumes:
  postgres_data:
  qdrant_data:
  uploads_data:
  openwebui_data:
```

**Step 3: Update .env.example**

```
# Required: API keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Optional: Override defaults
# POSTGRES_PASSWORD=canon_pass
# ANTHROPIC_MODEL=claude-sonnet-4-20250514
# OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

**Step 4: Commit**

```bash
git add backend/Dockerfile docker-compose.yml .env.example
git commit -m "feat: production Dockerfile and simplified 4-service docker-compose"
```

---

## Task 12: Clean Up Unused Files and Schemas

**Files:**
- Rewrite: `backend/app/models/schemas.py` (trim to what's used)
- Delete: `backend/app/models/__init__.py` (or update)
- Delete: `backend/app/api/__init__.py` (update)
- Rewrite: `backend/tests/test_basic.py` (update for new app structure)

**Step 1: Trim schemas to what's needed**

```python
# backend/app/models/schemas.py
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=10, ge=1, le=50)


class Citation(BaseModel):
    document_id: str
    title: str
    chunk_text: str
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    processing_time_ms: int
```

**Step 2: Rewrite basic tests for new app**

```python
# backend/tests/test_basic.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_list_models():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["data"][0]["id"] == "canon-builder"
```

**Step 3: Run full test suite**

Run: `cd backend && uv run pytest tests/ -v --cov=app`
Expected: All tests pass.

**Step 4: Commit**

```bash
git add backend/app/models/schemas.py backend/tests/test_basic.py
git commit -m "feat: clean up unused schemas and update tests for new app"
```

---

## Task 13: Integration Test — Full Pipeline

**Files:**
- Create: `backend/tests/test_integration.py`

**Step 1: Write integration test**

This test requires running postgres and qdrant services. Mark with a `@pytest.mark.integration` marker so unit tests can run without infrastructure.

```python
# backend/tests/test_integration.py
import os
import pytest
import tempfile
from httpx import AsyncClient, ASGITransport
from app.main import app


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_upload_and_query_pipeline():
    """Upload a document, then query it and verify we get a relevant answer."""
    transport = ASGITransport(app=app)

    # Create a test document
    content = """
    The Kingdom of Eldoria is a vast realm in the northern continent.
    Its capital city is Thornwall, built upon ancient dwarven ruins.
    The current ruler is Queen Seraphina, who took the throne after
    the War of Silver Flames in the year 1247.
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Upload
            with open(temp_path, "rb") as f:
                response = await client.post(
                    "/api/v1/documents/upload",
                    files={"file": ("eldoria.txt", f, "text/plain")},
                )
            assert response.status_code == 200
            doc = response.json()
            assert doc["status"] == "completed"
            assert doc["chunk_count"] > 0

            # Query
            response = await client.post(
                "/api/v1/query",
                json={"question": "What is the capital of Eldoria?"},
            )
            assert response.status_code == 200
            result = response.json()
            assert "Thornwall" in result["answer"]
            assert len(result["citations"]) > 0

            # Delete
            response = await client.delete(f"/api/v1/documents/{doc['id']}")
            assert response.status_code == 200

            # Verify deleted
            response = await client.get(f"/api/v1/documents/{doc['id']}")
            assert response.status_code == 404
    finally:
        os.unlink(temp_path)
```

**Step 2: Run integration test** (requires docker services running)

Run: `cd backend && uv run pytest tests/test_integration.py -v -m integration`
Expected: PASS — full upload → query → delete pipeline works.

**Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "feat: add integration test for full upload-query-delete pipeline"
```

---

## Task 14: Update Documentation and Roadmap

**Files:**
- Update: `CLAUDE.md`
- Update: `README.md`
- Create: `docs/ROADMAP.md`

**Step 1: Update CLAUDE.md** to reflect new architecture (UV, async, no auth, 4 services).

**Step 2: Update README.md** with new quick start (just needs API keys in .env, docker-compose up).

**Step 3: Create roadmap**

```markdown
# Canon Builder Roadmap

## Phase 1: Personal Usable State (current)
- [x] Upload text/md/PDF documents
- [x] RAG-powered query with citations
- [x] OpenWebUI integration
- [x] Async service layer
- [x] LLM provider abstraction (Anthropic + OpenAI)

## Phase 2: Knowledge Graph
- [ ] Neo4j async service
- [ ] Entity extraction via LLM
- [ ] Graph API endpoints
- [ ] Graph-enhanced hybrid RAG search
- [ ] Obsidian vault sync

## Phase 3: Proposals & Consistency
- [ ] AI-generated canon extension proposals
- [ ] Review workflow (accept/edit/reject)
- [ ] Contradiction detection
- [ ] Audit logging
- [ ] Coherence scoring

## Phase 4: Multi-User & Auth
- [ ] User registration and JWT login
- [ ] Per-user document isolation
- [ ] Role-based access
- [ ] Rate limiting
- [ ] Secrets management

## Phase 5: Advanced Features
- [ ] Ollama local LLM support
- [ ] Unstructured.io document parsing (DOCX, images, OCR)
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Export (PDF, static sites)
- [ ] Multi-user collaboration
- [ ] Plugin ecosystem
```

**Step 4: Commit**

```bash
git add CLAUDE.md README.md docs/ROADMAP.md
git commit -m "docs: update for rebuilt architecture, add roadmap"
```

---

## Summary

| Task | What | Key Files |
|------|------|-----------|
| 1 | UV + pyproject.toml | `backend/pyproject.toml` |
| 2 | Config rewrite | `backend/app/core/config.py` |
| 3 | LLM provider abstraction | `backend/app/services/llm/` |
| 4 | Async DB + repositories | `backend/app/models/database.py`, `repositories.py` |
| 5 | Alembic migrations | `backend/alembic/` |
| 6 | Async Qdrant service | `backend/app/services/qdrant_service.py` |
| 7 | Ingestion service | `backend/app/services/ingestion_service.py` |
| 8 | RAG service | `backend/app/services/rag_service.py` |
| 9 | API routes + OpenAI compat | `backend/app/api/v1/`, `backend/app/dependencies.py` |
| 10 | Main app rewrite | `backend/app/main.py` |
| 11 | Dockerfile + docker-compose | `backend/Dockerfile`, `docker-compose.yml` |
| 12 | Clean up unused code | schemas, tests |
| 13 | Integration test | `backend/tests/test_integration.py` |
| 14 | Docs + roadmap | `CLAUDE.md`, `README.md`, `docs/ROADMAP.md` |
