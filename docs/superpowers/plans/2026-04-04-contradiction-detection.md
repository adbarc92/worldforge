# Contradiction Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically detect contradictions between document chunks in a project's canon and queue them for manual resolution.

**Architecture:** New `contradictions` table stores detected conflicts with text snapshots. A `ContradictionService` uses Qdrant similarity search to find candidate pairs and the LLM to classify them. Detection runs as a fire-and-forget `asyncio.create_task()` after document ingestion, with an on-demand full-scan endpoint. Frontend adds a Contradictions page with side-by-side conflict view.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Qdrant, Anthropic Claude (classification), React + TanStack Query, shadcn/ui

**Spec:** `docs/superpowers/specs/2026-04-04-contradiction-detection-design.md`

---

## File Structure

### Backend — New Files
- `backend/alembic/versions/20260404_contradictions.py` — Migration adding contradictions table
- `backend/app/models/contradiction.py` — SQLAlchemy Contradiction model
- `backend/app/models/contradiction_repository.py` — Repository with CRUD + dedup check
- `backend/app/services/contradiction_service.py` — Detection logic, scanning, LLM classification
- `backend/app/api/v1/contradictions.py` — API route handlers
- `backend/tests/test_contradiction_service.py` — Service unit tests
- `backend/tests/test_contradiction_api.py` — API endpoint tests

### Backend — Modified Files
- `backend/app/models/database.py` — Import new model so Alembic sees it
- `backend/app/dependencies.py` — Add `get_contradiction_service()`
- `backend/app/services/ingestion_service.py` — Fire background scan after ingestion
- `backend/app/main.py` — Register contradictions router

### Frontend — New Files
- `frontend/src/hooks/useContradictions.ts` — React Query hooks
- `frontend/src/pages/ContradictionsPage.tsx` — Main page component
- `frontend/src/components/contradictions/ContradictionCard.tsx` — Individual card

### Frontend — Modified Files
- `frontend/src/lib/api.ts` — Add contradictions API methods
- `frontend/src/App.tsx` — Add route
- `frontend/src/components/layout/Sidebar.tsx` — Add nav link

---

## Task 1: Database Migration & Model

**Files:**
- Create: `backend/alembic/versions/20260404_contradictions.py`
- Create: `backend/app/models/contradiction.py`
- Modify: `backend/app/models/database.py:1-3` (add import)

- [ ] **Step 1: Create the Contradiction model**

Create `backend/app/models/contradiction.py`:

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.models.database import Base


class Contradiction(Base):
    __tablename__ = "contradictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chunk_a_id = Column(String, nullable=False)
    chunk_b_id = Column(String, nullable=False)
    document_a_id = Column(String, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    document_b_id = Column(String, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    document_a_title = Column(String, nullable=False, default="")
    document_b_title = Column(String, nullable=False, default="")
    chunk_a_text = Column(Text, nullable=False)
    chunk_b_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="open")
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Import the model in database.py so Alembic discovers it**

In `backend/app/models/database.py`, add after the existing imports at the top:

```python
import app.models.contradiction  # noqa: F401 — ensure Alembic sees the model
```

This import goes after the `Base = declarative_base()` line and existing model definitions, at the end of the file.

- [ ] **Step 3: Create the Alembic migration**

Create `backend/alembic/versions/20260404_contradictions.py`:

```python
"""Add contradictions table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contradictions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_a_id", sa.String(), nullable=False),
        sa.Column("chunk_b_id", sa.String(), nullable=False),
        sa.Column("document_a_id", sa.String(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_b_id", sa.String(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_a_title", sa.String(), nullable=False, server_default=""),
        sa.Column("document_b_title", sa.String(), nullable=False, server_default=""),
        sa.Column("chunk_a_text", sa.Text(), nullable=False),
        sa.Column("chunk_b_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("contradictions")
```

- [ ] **Step 4: Verify migration applies**

Run:
```bash
cd backend && uv run alembic upgrade head
```

Expected: Migration applies without errors.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/contradiction.py backend/alembic/versions/20260404_contradictions.py backend/app/models/database.py
git commit -m "feat: add contradictions table and model"
```

---

## Task 2: Contradiction Repository

**Files:**
- Create: `backend/app/models/contradiction_repository.py`

- [ ] **Step 1: Write the repository**

Create `backend/app/models/contradiction_repository.py`:

```python
from datetime import datetime, timezone
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contradiction import Contradiction


class ContradictionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: str,
        chunk_a_id: str,
        chunk_b_id: str,
        document_a_id: str,
        document_b_id: str,
        document_a_title: str,
        document_b_title: str,
        chunk_a_text: str,
        chunk_b_text: str,
        explanation: str,
    ) -> Contradiction:
        contradiction = Contradiction(
            project_id=project_id,
            chunk_a_id=chunk_a_id,
            chunk_b_id=chunk_b_id,
            document_a_id=document_a_id,
            document_b_id=document_b_id,
            document_a_title=document_a_title,
            document_b_title=document_b_title,
            chunk_a_text=chunk_a_text,
            chunk_b_text=chunk_b_text,
            explanation=explanation,
        )
        self.db.add(contradiction)
        await self.db.commit()
        await self.db.refresh(contradiction)
        return contradiction

    async def pair_exists(self, chunk_a_id: str, chunk_b_id: str) -> bool:
        """Check if a contradiction between these two chunks already exists (in either order)."""
        stmt = select(func.count()).select_from(Contradiction).where(
            or_(
                and_(Contradiction.chunk_a_id == chunk_a_id, Contradiction.chunk_b_id == chunk_b_id),
                and_(Contradiction.chunk_a_id == chunk_b_id, Contradiction.chunk_b_id == chunk_a_id),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() > 0

    async def list(
        self, project_id: str, status: str | None = "open", skip: int = 0, limit: int = 50
    ) -> list[Contradiction]:
        stmt = select(Contradiction).where(Contradiction.project_id == project_id)
        if status:
            stmt = stmt.where(Contradiction.status == status)
        stmt = stmt.order_by(Contradiction.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, project_id: str, status: str | None = "open") -> int:
        stmt = select(func.count()).select_from(Contradiction).where(Contradiction.project_id == project_id)
        if status:
            stmt = stmt.where(Contradiction.status == status)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get(self, contradiction_id: str) -> Contradiction | None:
        stmt = select(Contradiction).where(Contradiction.id == contradiction_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, contradiction_id: str, status: str) -> Contradiction | None:
        contradiction = await self.get(contradiction_id)
        if not contradiction:
            return None
        contradiction.status = status
        if status in ("resolved", "dismissed"):
            contradiction.resolved_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(contradiction)
        return contradiction
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/contradiction_repository.py
git commit -m "feat: add contradiction repository with dedup check"
```

---

## Task 3: Contradiction Service

**Files:**
- Create: `backend/app/services/contradiction_service.py`
- Create: `backend/tests/test_contradiction_service.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_contradiction_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.contradiction_service import ContradictionService


@pytest.fixture
def mock_llm_service():
    llm = AsyncMock()
    return llm


@pytest.fixture
def mock_qdrant_service():
    qdrant = AsyncMock()
    return qdrant


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.pair_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def service(mock_llm_service, mock_qdrant_service, mock_repo):
    return ContradictionService(
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service,
        repo=mock_repo,
    )


@pytest.mark.asyncio
async def test_classify_contradiction_positive(service, mock_llm_service):
    mock_llm_service.generate.return_value = '{"is_contradiction": true, "explanation": "Chunk A says X, Chunk B says Y"}'
    result = await service.classify_pair("Passage A text", "Passage B text")
    assert result["is_contradiction"] is True
    assert "Chunk A says X" in result["explanation"]


@pytest.mark.asyncio
async def test_classify_contradiction_negative(service, mock_llm_service):
    mock_llm_service.generate.return_value = '{"is_contradiction": false, "explanation": "No conflict"}'
    result = await service.classify_pair("Passage A text", "Passage B text")
    assert result["is_contradiction"] is False


@pytest.mark.asyncio
async def test_classify_handles_markdown_wrapped_json(service, mock_llm_service):
    mock_llm_service.generate.return_value = '```json\n{"is_contradiction": true, "explanation": "conflict"}\n```'
    result = await service.classify_pair("A", "B")
    assert result["is_contradiction"] is True


@pytest.mark.asyncio
async def test_classify_handles_malformed_json(service, mock_llm_service):
    mock_llm_service.generate.return_value = "This is not JSON at all"
    result = await service.classify_pair("A", "B")
    assert result["is_contradiction"] is False


@pytest.mark.asyncio
async def test_scan_document_skips_same_document_chunks(service, mock_qdrant_service, mock_repo):
    # New document's chunks
    mock_qdrant_service.search.side_effect = [
        # For chunk 1 of new doc, return a match from the SAME document
        [{"id": "other-chunk", "score": 0.9, "payload": {"document_id": "doc-1", "text": "similar text"}}],
    ]
    # The new doc's chunks retrieved from Qdrant
    with patch.object(service, "_get_document_chunks") as mock_get:
        mock_get.return_value = [
            {"id": "chunk-1", "text": "some text", "document_id": "doc-1", "project_id": "proj-1"}
        ]
        await service.scan_document("doc-1", "proj-1")

    # Should NOT have called classify since the match is from the same document
    service.llm_service.generate.assert_not_called()
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_scan_document_skips_existing_pairs(service, mock_qdrant_service, mock_llm_service, mock_repo):
    mock_repo.pair_exists.return_value = True
    mock_qdrant_service.search.return_value = [
        {"id": "other-chunk", "score": 0.9, "payload": {"document_id": "doc-2", "text": "conflict text"}}
    ]
    with patch.object(service, "_get_document_chunks") as mock_get:
        mock_get.return_value = [
            {"id": "chunk-1", "text": "some text", "document_id": "doc-1", "project_id": "proj-1"}
        ]
        await service.scan_document("doc-1", "proj-1")

    mock_llm_service.generate.assert_not_called()
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_scan_document_creates_contradiction(service, mock_qdrant_service, mock_llm_service, mock_repo):
    mock_llm_service.generate.return_value = '{"is_contradiction": true, "explanation": "They conflict"}'
    mock_qdrant_service.search.return_value = [
        {"id": "other-chunk", "score": 0.9, "payload": {"document_id": "doc-2", "text": "conflict text"}}
    ]
    with patch.object(service, "_get_document_chunks") as mock_get:
        mock_get.return_value = [
            {"id": "chunk-1", "text": "some text", "document_id": "doc-1", "project_id": "proj-1"}
        ]
        await service.scan_document("doc-1", "proj-1")

    mock_repo.create.assert_called_once()
    call_kwargs = mock_repo.create.call_args.kwargs
    assert call_kwargs["chunk_a_id"] == "chunk-1"
    assert call_kwargs["chunk_b_id"] == "other-chunk"
    assert call_kwargs["document_a_title"] == ""
    assert call_kwargs["document_b_title"] == ""
    assert call_kwargs["explanation"] == "They conflict"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd backend && uv run pytest tests/test_contradiction_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.contradiction_service'`

- [ ] **Step 3: Write the ContradictionService**

Create `backend/app/services/contradiction_service.py`:

```python
import json
import logging
import re

from app.models.contradiction_repository import ContradictionRepository
from app.services.llm.service import LLMService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are comparing passages from a worldbuilding canon. Do these two passages contradict each other? A contradiction means they assert mutually exclusive facts about the same subject. Different levels of detail, different topics, or evolving ideas are NOT contradictions.

Passage A:
{chunk_a_text}

Passage B:
{chunk_b_text}

Respond with JSON only: {{"is_contradiction": bool, "explanation": "string"}}"""

SIMILAR_CHUNKS_TOP_K = 5


class ContradictionService:
    def __init__(
        self,
        llm_service: LLMService,
        qdrant_service: QdrantService,
        repo: ContradictionRepository,
    ):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.repo = repo

    async def classify_pair(self, chunk_a_text: str, chunk_b_text: str) -> dict:
        """Ask the LLM whether two passages contradict each other."""
        prompt = CLASSIFICATION_PROMPT.format(
            chunk_a_text=chunk_a_text,
            chunk_b_text=chunk_b_text,
        )
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0,
                max_tokens=256,
            )
            return self._parse_classification(response)
        except Exception:
            logger.exception("LLM classification failed")
            return {"is_contradiction": False, "explanation": ""}

    def _parse_classification(self, response: str) -> dict:
        """Parse LLM JSON response, handling markdown wrapping."""
        text = response.strip()
        # Strip markdown code fences if present
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        try:
            data = json.loads(text)
            return {
                "is_contradiction": bool(data.get("is_contradiction", False)),
                "explanation": str(data.get("explanation", "")),
            }
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Failed to parse LLM classification response: %s", response[:200])
            return {"is_contradiction": False, "explanation": ""}

    async def _get_document_chunks(self, document_id: str) -> list[dict]:
        """Retrieve all chunks for a document from Qdrant."""
        results = await self.qdrant_service.search_by_filter(
            filters={"document_id": document_id},
            limit=1000,
        )
        return results

    async def scan_document(self, document_id: str, project_id: str) -> int:
        """Scan a single document's chunks against the rest of the project. Returns count of new contradictions found."""
        chunks = await self._get_document_chunks(document_id)
        if not chunks:
            return 0

        found = 0
        for chunk in chunks:
            chunk_vector = await self.llm_service.embed([chunk["text"]])
            similar = await self.qdrant_service.search(
                query_vector=chunk_vector[0],
                top_k=SIMILAR_CHUNKS_TOP_K,
                filters={"project_id": project_id},
            )

            for match in similar:
                match_doc_id = match["payload"].get("document_id", "")
                # Skip chunks from the same document
                if match_doc_id == document_id:
                    continue

                # Skip if this pair already exists
                if await self.repo.pair_exists(chunk["id"], match["id"]):
                    continue

                classification = await self.classify_pair(
                    chunk["text"],
                    match["payload"]["text"],
                )

                if classification["is_contradiction"]:
                    await self.repo.create(
                        project_id=project_id,
                        chunk_a_id=chunk["id"],
                        chunk_b_id=match["id"],
                        document_a_id=document_id,
                        document_b_id=match_doc_id,
                        document_a_title=chunk.get("title", ""),
                        document_b_title=match["payload"].get("title", ""),
                        chunk_a_text=chunk["text"],
                        chunk_b_text=match["payload"]["text"],
                        explanation=classification["explanation"],
                    )
                    found += 1

        logger.info("Scanned document %s: found %d contradictions", document_id, found)
        return found

    async def scan_project(self, project_id: str) -> int:
        """Scan all documents in a project for contradictions. Returns total new contradictions found."""
        from app.models.repositories import DocumentRepository

        # We need to get all document IDs for this project
        # The caller provides a db session via the repo, so we reuse that
        doc_repo = DocumentRepository(self.repo.db)
        documents = await doc_repo.list(project_id=project_id, skip=0, limit=10000)

        total = 0
        for doc in documents:
            if doc.status != "completed":
                continue
            count = await self.scan_document(doc.id, project_id)
            total += count

        logger.info("Project scan complete for %s: found %d total contradictions", project_id, total)
        return total
```

- [ ] **Step 4: Add `search_by_filter` to QdrantService**

This method is needed by ContradictionService to retrieve all chunks for a document. Add to `backend/app/services/qdrant_service.py` after the existing `search` method:

```python
    async def search_by_filter(self, filters: dict, limit: int = 100) -> list[dict]:
        """Retrieve points matching a filter (no vector query)."""
        must = [
            models.FieldCondition(key=k, match=models.MatchValue(value=v))
            for k, v in filters.items()
        ]
        query_filter = models.Filter(must=must)
        points, _ = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter,
            limit=limit,
            with_vectors=False,
            with_payload=True,
        )
        return [
            {"id": str(p.id), "text": p.payload.get("text", ""), "document_id": p.payload.get("document_id", ""), "title": p.payload.get("title", ""), "project_id": p.payload.get("project_id", "")}
            for p in points
        ]
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd backend && uv run pytest tests/test_contradiction_service.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/contradiction_service.py backend/app/services/qdrant_service.py backend/tests/test_contradiction_service.py
git commit -m "feat: add contradiction detection service with LLM classification"
```

---

## Task 4: API Endpoints

**Files:**
- Create: `backend/app/api/v1/contradictions.py`
- Create: `backend/tests/test_contradiction_api.py`
- Modify: `backend/app/dependencies.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add `get_contradiction_service` to dependencies**

Add to `backend/app/dependencies.py` after the `get_rag_service` function:

```python
from app.models.contradiction_repository import ContradictionRepository
from app.services.contradiction_service import ContradictionService


async def get_contradiction_service(
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> ContradictionService:
    repo = ContradictionRepository(db)
    return ContradictionService(
        llm_service=llm_service,
        qdrant_service=qdrant_service,
        repo=repo,
    )
```

Also add the necessary import at the top:
```python
from app.models.database import get_db, AsyncSession
```

(Check if `AsyncSession` and `get_db` are already imported — if so, just add the new ones.)

- [ ] **Step 2: Write the API routes**

Create `backend/app/api/v1/contradictions.py`:

```python
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.project_repository import ProjectRepository
from app.models.contradiction_repository import ContradictionRepository
from app.dependencies import get_contradiction_service
from app.services.contradiction_service import ContradictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/contradictions", tags=["contradictions"])


async def _verify_project(project_id: str, db: AsyncSession):
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("")
async def list_contradictions(
    project_id: str,
    status: str | None = "open",
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = ContradictionRepository(db)
    contradictions = await repo.list(project_id=project_id, status=status, skip=skip, limit=limit)
    count = await repo.count(project_id=project_id, status=status)
    return {
        "items": [
            {
                "id": c.id,
                "chunk_a_text": c.chunk_a_text,
                "chunk_b_text": c.chunk_b_text,
                "document_a_id": c.document_a_id,
                "document_b_id": c.document_b_id,
                "document_a_title": c.document_a_title,
                "document_b_title": c.document_b_title,
                "explanation": c.explanation,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            }
            for c in contradictions
        ],
        "total": count,
    }


@router.post("/scan", status_code=202)
async def scan_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    contradiction_service: ContradictionService = Depends(get_contradiction_service),
):
    await _verify_project(project_id, db)

    async def _run_scan():
        try:
            from app.models.database import async_session
            async with async_session() as session:
                repo = ContradictionRepository(session)
                svc = ContradictionService(
                    llm_service=contradiction_service.llm_service,
                    qdrant_service=contradiction_service.qdrant_service,
                    repo=repo,
                )
                count = await svc.scan_project(project_id)
                logger.info("Background project scan found %d contradictions", count)
        except Exception:
            logger.exception("Background project scan failed for %s", project_id)

    asyncio.create_task(_run_scan())
    return {"status": "scan_started", "project_id": project_id}


@router.patch("/{contradiction_id}/resolve")
async def resolve_contradiction(
    project_id: str,
    contradiction_id: str,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = ContradictionRepository(db)
    contradiction = await repo.update_status(contradiction_id, "resolved")
    if not contradiction:
        raise HTTPException(status_code=404, detail="Contradiction not found")
    return {"id": contradiction.id, "status": contradiction.status}


@router.patch("/{contradiction_id}/dismiss")
async def dismiss_contradiction(
    project_id: str,
    contradiction_id: str,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = ContradictionRepository(db)
    contradiction = await repo.update_status(contradiction_id, "dismissed")
    if not contradiction:
        raise HTTPException(status_code=404, detail="Contradiction not found")
    return {"id": contradiction.id, "status": contradiction.status}
```

- [ ] **Step 3: Export `async_session` from database.py**

The background task in the scan endpoint needs to create its own session. Verify that `async_session` (the `async_sessionmaker` instance) is accessible. In `backend/app/models/database.py`, the session factory is created. Ensure it's importable as `async_session`. Check the current name — if it's named differently (e.g., `AsyncSessionLocal`), use that name in the contradictions route instead.

- [ ] **Step 4: Register the router in main.py**

In `backend/app/main.py`, add the import and router registration alongside existing routers:

```python
from app.api.v1.contradictions import router as contradictions_router
```

And in the router registration section (around line 112):

```python
app.include_router(contradictions_router, prefix="/api/v1")
```

- [ ] **Step 5: Write API tests**

Create `backend/tests/test_contradiction_api.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session


@pytest.fixture
def sample_contradiction():
    c = MagicMock()
    c.id = "cont-1"
    c.project_id = "proj-1"
    c.chunk_a_text = "The sky is blue"
    c.chunk_b_text = "The sky is green"
    c.document_a_id = "doc-1"
    c.document_b_id = "doc-2"
    c.document_a_title = "Weather.md"
    c.document_b_title = "Climate.md"
    c.explanation = "Conflicting sky colors"
    c.status = "open"
    c.created_at = datetime(2026, 4, 4, tzinfo=timezone.utc)
    c.resolved_at = None
    return c


@pytest.mark.asyncio
async def test_list_contradictions(sample_contradiction):
    with patch("app.api.v1.contradictions._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo:
        mock_repo = AsyncMock()
        mock_repo.list.return_value = [sample_contradiction]
        mock_repo.count.return_value = 1
        MockRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/proj-1/contradictions?status=open")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == "cont-1"
        assert data["items"][0]["explanation"] == "Conflicting sky colors"


@pytest.mark.asyncio
async def test_scan_returns_202():
    with patch("app.api.v1.contradictions._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.contradictions.get_contradiction_service") as mock_get_svc:
        mock_svc = AsyncMock()
        mock_get_svc.return_value = mock_svc
        # Patch asyncio.create_task to prevent actual background work
        with patch("app.api.v1.contradictions.asyncio.create_task"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/v1/projects/proj-1/contradictions/scan")

        assert resp.status_code == 202
        assert resp.json()["status"] == "scan_started"


@pytest.mark.asyncio
async def test_resolve_contradiction(sample_contradiction):
    sample_contradiction.status = "resolved"
    with patch("app.api.v1.contradictions._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo:
        mock_repo = AsyncMock()
        mock_repo.update_status.return_value = sample_contradiction
        MockRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch("/api/v1/projects/proj-1/contradictions/cont-1/resolve")

        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_dismiss_contradiction(sample_contradiction):
    sample_contradiction.status = "dismissed"
    with patch("app.api.v1.contradictions._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo:
        mock_repo = AsyncMock()
        mock_repo.update_status.return_value = sample_contradiction
        MockRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch("/api/v1/projects/proj-1/contradictions/cont-1/dismiss")

        assert resp.status_code == 200
        assert resp.json()["status"] == "dismissed"


@pytest.mark.asyncio
async def test_resolve_nonexistent_returns_404():
    with patch("app.api.v1.contradictions._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo:
        mock_repo = AsyncMock()
        mock_repo.update_status.return_value = None
        MockRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch("/api/v1/projects/proj-1/contradictions/bad-id/resolve")

        assert resp.status_code == 404
```

- [ ] **Step 6: Run all tests**

Run:
```bash
cd backend && uv run pytest tests/test_contradiction_api.py tests/test_contradiction_service.py -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/contradictions.py backend/app/dependencies.py backend/app/main.py backend/app/models/database.py backend/tests/test_contradiction_api.py
git commit -m "feat: add contradiction API endpoints (list, scan, resolve, dismiss)"
```

---

## Task 5: Hook Into Ingestion Pipeline

**Files:**
- Modify: `backend/app/services/ingestion_service.py:26-65`
- Modify: `backend/app/api/v1/documents.py:25-57`

- [ ] **Step 1: Add background scan trigger to the upload endpoint**

The ingestion service itself stays unchanged — we fire the background task from the upload route handler, after ingestion succeeds. This avoids coupling the ingestion service to the contradiction service.

Modify `backend/app/api/v1/documents.py` — update the `upload_document` function:

```python
import asyncio
import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.repositories import DocumentRepository
from app.models.project_repository import ProjectRepository
from app.core.config import settings
from app.dependencies import get_ingestion_service, get_contradiction_service
from app.services.contradiction_service import ContradictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


async def _verify_project(project_id: str, db: AsyncSession):
    """Verify project exists, raise 404 if not."""
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/upload")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    ingestion_service=Depends(get_ingestion_service),
    contradiction_service: ContradictionService = Depends(get_contradiction_service),
):
    await _verify_project(project_id, db)

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
    doc = await ingestion_service.process_document(
        file_path=file_path, title=title, project_id=project_id
    )

    # Fire background contradiction scan
    async def _scan_background():
        try:
            from app.models.database import async_session
            from app.models.contradiction_repository import ContradictionRepository
            async with async_session() as session:
                repo = ContradictionRepository(session)
                svc = ContradictionService(
                    llm_service=contradiction_service.llm_service,
                    qdrant_service=contradiction_service.qdrant_service,
                    repo=repo,
                )
                count = await svc.scan_document(doc.id, project_id)
                logger.info("Background scan for '%s' found %d contradictions", title, count)
        except Exception:
            logger.exception("Background contradiction scan failed for '%s'", title)

    asyncio.create_task(_scan_background())

    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "project_id": project_id,
    }
```

Keep the `import os, uuid, aiofiles` that already exist at the top.

- [ ] **Step 2: Run existing tests to verify nothing is broken**

Run:
```bash
cd backend && uv run pytest tests/ -v
```

Expected: All existing tests still PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/documents.py
git commit -m "feat: trigger background contradiction scan after document upload"
```

---

## Task 6: Frontend API Client & Hooks

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/useContradictions.ts`

- [ ] **Step 1: Add contradiction types and API methods**

Add the following interface to `frontend/src/lib/api.ts` after the existing interface definitions (around line 49):

```typescript
export interface Contradiction {
  id: string;
  chunk_a_text: string;
  chunk_b_text: string;
  document_a_id: string | null;
  document_b_id: string | null;
  document_a_title: string;
  document_b_title: string;
  explanation: string;
  status: "open" | "resolved" | "dismissed";
  created_at: string;
  resolved_at: string | null;
}

export interface ContradictionList {
  items: Contradiction[];
  total: number;
}
```

Add the `contradictions` namespace to the `api` object (after the `query` section):

```typescript
  contradictions: {
    list: (projectId: string, status = "open", skip = 0, limit = 50) =>
      request<ContradictionList>(
        `/api/v1/projects/${projectId}/contradictions?status=${status}&skip=${skip}&limit=${limit}`
      ),
    scan: (projectId: string) =>
      request<{ status: string; project_id: string }>(
        `/api/v1/projects/${projectId}/contradictions/scan`,
        { method: "POST" }
      ),
    resolve: (projectId: string, id: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/projects/${projectId}/contradictions/${id}/resolve`,
        { method: "PATCH" }
      ),
    dismiss: (projectId: string, id: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/projects/${projectId}/contradictions/${id}/dismiss`,
        { method: "PATCH" }
      ),
  },
```

- [ ] **Step 2: Create the React Query hooks**

Create `frontend/src/hooks/useContradictions.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useActiveProject } from "../hooks/useActiveProject";

export function useContradictions(status: string = "open") {
  const { projectId } = useActiveProject();
  return useQuery({
    queryKey: ["contradictions", projectId, status],
    queryFn: () => api.contradictions.list(projectId!, status),
    enabled: !!projectId,
  });
}

export function useScanContradictions() {
  const { projectId } = useActiveProject();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.contradictions.scan(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contradictions", projectId] });
    },
  });
}

export function useResolveContradiction() {
  const { projectId } = useActiveProject();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.contradictions.resolve(projectId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contradictions", projectId] });
    },
  });
}

export function useDismissContradiction() {
  const { projectId } = useActiveProject();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.contradictions.dismiss(projectId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contradictions", projectId] });
    },
  });
}
```

- [ ] **Step 3: Verify frontend builds**

Run:
```bash
cd frontend && npm run build
```

Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/hooks/useContradictions.ts
git commit -m "feat: add contradiction API client and React Query hooks"
```

---

## Task 7: Frontend Contradictions Page

**Files:**
- Create: `frontend/src/components/contradictions/ContradictionCard.tsx`
- Create: `frontend/src/pages/ContradictionsPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create the ContradictionCard component**

Create `frontend/src/components/contradictions/ContradictionCard.tsx`:

```tsx
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import type { Contradiction } from "../../lib/api";

interface ContradictionCardProps {
  contradiction: Contradiction;
  onResolve: (id: string) => void;
  onDismiss: (id: string) => void;
}

export function ContradictionCard({ contradiction, onResolve, onDismiss }: ContradictionCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              {contradiction.document_a_title || "Passage A"}
            </p>
            <p className="text-sm bg-muted rounded p-3">{contradiction.chunk_a_text}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              {contradiction.document_b_title || "Passage B"}
            </p>
            <p className="text-sm bg-muted rounded p-3">{contradiction.chunk_b_text}</p>
          </div>
        </div>
        <p className="text-sm mb-4">
          <span className="font-medium">Explanation:</span> {contradiction.explanation}
        </p>
        {contradiction.status === "open" && (
          <div className="flex gap-2">
            <Button size="sm" onClick={() => onResolve(contradiction.id)}>
              Resolve
            </Button>
            <Button size="sm" variant="outline" onClick={() => onDismiss(contradiction.id)}>
              Dismiss
            </Button>
          </div>
        )}
        {contradiction.status !== "open" && (
          <p className="text-xs text-muted-foreground">
            {contradiction.status === "resolved" ? "Resolved" : "Dismissed"}
            {contradiction.resolved_at && ` on ${new Date(contradiction.resolved_at).toLocaleDateString()}`}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Create the ContradictionsPage**

Create `frontend/src/pages/ContradictionsPage.tsx`:

```tsx
import { useState } from "react";
import { Button } from "../components/ui/button";
import { ContradictionCard } from "../components/contradictions/ContradictionCard";
import {
  useContradictions,
  useScanContradictions,
  useResolveContradiction,
  useDismissContradiction,
} from "../hooks/useContradictions";
import { toast } from "sonner";

const TABS = ["open", "resolved", "dismissed"] as const;

export default function ContradictionsPage() {
  const [activeTab, setActiveTab] = useState<string>("open");
  const { data, isLoading } = useContradictions(activeTab);
  const scan = useScanContradictions();
  const resolve = useResolveContradiction();
  const dismiss = useDismissContradiction();

  const handleScan = () => {
    scan.mutate(undefined, {
      onSuccess: () => toast.info("Scanning for contradictions... Refresh in a moment to see results."),
      onError: () => toast.error("Failed to start scan"),
    });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Contradictions</h1>
          {data && <p className="text-sm text-muted-foreground">{data.total} {activeTab}</p>}
        </div>
        <Button onClick={handleScan} disabled={scan.isPending}>
          {scan.isPending ? "Starting scan..." : "Scan Project"}
        </Button>
      </div>

      <div className="flex gap-1 mb-6">
        {TABS.map((tab) => (
          <Button
            key={tab}
            variant={activeTab === tab ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </Button>
        ))}
      </div>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No {activeTab} contradictions.</p>
      )}

      <div className="space-y-4">
        {data?.items.map((c) => (
          <ContradictionCard
            key={c.id}
            contradiction={c}
            onResolve={(id) => resolve.mutate(id)}
            onDismiss={(id) => dismiss.mutate(id)}
          />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add the route to App.tsx**

In `frontend/src/App.tsx`, add the import:

```typescript
import ContradictionsPage from "./pages/ContradictionsPage";
```

Add the route inside the `<Route element={<Shell />}>` block, after the documents route:

```tsx
<Route path="/contradictions" element={<ContradictionsPage />} />
```

- [ ] **Step 4: Add the sidebar link**

In `frontend/src/components/layout/Sidebar.tsx`, add to the `links` array after Documents:

```typescript
{ to: "/contradictions", label: "Contradictions", icon: "\u26A0\uFE0F" },
```

(Unicode for the warning sign emoji)

- [ ] **Step 5: Verify frontend builds**

Run:
```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/contradictions/ContradictionCard.tsx frontend/src/pages/ContradictionsPage.tsx frontend/src/App.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "feat: add contradictions page with scan, resolve, dismiss UI"
```

---

## Task 8: End-to-End Verification

**Files:** None (testing only)

- [ ] **Step 1: Rebuild and restart Docker**

```bash
cd D:/MajorProjects/CURRENT/worldforge && docker compose up -d --build
```

Wait for the API to be healthy:
```bash
curl http://localhost:8080/health
```

- [ ] **Step 2: Run all backend tests**

```bash
cd backend && uv run pytest tests/ -v
```

Expected: All tests PASS (existing + new).

- [ ] **Step 3: Verify the contradictions endpoints work**

Create a project and check the contradictions endpoint responds:

```bash
# List contradictions for the existing Disruption project
curl -s http://localhost:8080/api/v1/projects/b568b15e-64db-408c-a408-65bf71948050/contradictions | python -m json.tool

# Trigger a scan
curl -s -X POST http://localhost:8080/api/v1/projects/b568b15e-64db-408c-a408-65bf71948050/contradictions/scan | python -m json.tool
```

Expected: List returns `{"items": [], "total": 0}`. Scan returns `{"status": "scan_started", ...}`.

- [ ] **Step 4: Verify the UI**

Open `http://localhost:8080/contradictions` in the browser. Verify:
- Contradictions page loads
- "Scan Project" button is visible
- Sidebar shows the Contradictions link

- [ ] **Step 5: Run a real contradiction scan**

Click "Scan Project" in the UI. Wait ~30-60 seconds, then refresh the page. Contradictions should appear if there are genuine conflicts in the uploaded Disruption documents.
