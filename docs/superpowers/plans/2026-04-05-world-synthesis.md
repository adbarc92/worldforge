# World Synthesis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a comprehensive narrative primer document summarizing a project's worldbuilding canon, gated behind all contradictions being resolved.

**Architecture:** New `syntheses` table stores generation state (outline, content, status). A `SynthesisService` orchestrates a multi-step LLM pipeline: batch-analyze chunks to propose an outline, then generate each section using relevant chunks and contradiction resolution notes. Background execution via `asyncio.create_task()`. Frontend adds a Synthesis page with outline editing, generation polling, markdown rendering, and download.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Qdrant, Anthropic Claude, React + TanStack Query, react-markdown, shadcn/ui

**Spec:** `docs/superpowers/specs/2026-04-05-world-synthesis-design.md`

---

## File Structure

### Backend — New Files
- `backend/alembic/versions/20260405_syntheses.py` — Migration adding syntheses table
- `backend/app/models/synthesis.py` — SQLAlchemy Synthesis model
- `backend/app/models/synthesis_repository.py` — Repository with CRUD + status transitions
- `backend/app/services/synthesis_service.py` — Outline generation, section generation, assembly
- `backend/app/api/v1/synthesis.py` — API route handlers
- `backend/tests/test_synthesis_service.py` — Service unit tests
- `backend/tests/test_synthesis_api.py` — API endpoint tests

### Backend — Modified Files
- `backend/app/models/database.py` — Import new model
- `backend/app/dependencies.py` — Add `get_synthesis_service()`
- `backend/app/api/v1/__init__.py` — Register synthesis router

### Frontend — New Files
- `frontend/src/hooks/useSynthesis.ts` — React Query hooks
- `frontend/src/pages/SynthesisPage.tsx` — Main page component
- `frontend/src/components/synthesis/OutlineEditor.tsx` — Editable outline list
- `frontend/src/components/synthesis/SynthesisViewer.tsx` — Rendered markdown view

### Frontend — Modified Files
- `frontend/src/lib/api.ts` — Add synthesis API methods
- `frontend/src/App.tsx` — Add route
- `frontend/src/components/layout/Sidebar.tsx` — Add nav link
- `package.json` — Add react-markdown + remark-gfm

---

## Task 1: Database Migration & Model

**Files:**
- Create: `backend/app/models/synthesis.py`
- Create: `backend/alembic/versions/20260405_syntheses.py`
- Modify: `backend/app/models/database.py:52`

- [ ] **Step 1: Create the Synthesis model**

Create `backend/app/models/synthesis.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Synthesis(Base):
    __tablename__ = "syntheses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="World Primer")
    outline: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    outline_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="outline_pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: Import the model in database.py**

Add at the end of `backend/app/models/database.py`, after the existing contradiction import:

```python
import app.models.synthesis  # noqa: F401
```

- [ ] **Step 3: Create the Alembic migration**

Create `backend/alembic/versions/20260405_syntheses.py`:

```python
"""Add syntheses table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "syntheses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False, server_default="World Primer"),
        sa.Column("outline", sa.JSON(), nullable=True),
        sa.Column("outline_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="outline_pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("syntheses")
```

- [ ] **Step 4: Verify migration chain**

```bash
cd backend && uv run alembic heads
```

Expected: Shows `d4e5f6a7b8c9 (head)` as the single head.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/synthesis.py backend/alembic/versions/20260405_syntheses.py backend/app/models/database.py
git commit -m "feat: add syntheses table and model"
```

---

## Task 2: Synthesis Repository

**Files:**
- Create: `backend/app/models/synthesis_repository.py`

- [ ] **Step 1: Create the repository**

Read `backend/app/models/contradiction_repository.py` first to match the existing pattern (uses `self.session`). Then create `backend/app/models/synthesis_repository.py`:

```python
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.synthesis import Synthesis


class SynthesisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project_id: str, title: str = "World Primer", auto: bool = False) -> Synthesis:
        synthesis = Synthesis(
            project_id=project_id,
            title=title,
            outline_approved=auto,
        )
        self.session.add(synthesis)
        await self.session.commit()
        await self.session.refresh(synthesis)
        return synthesis

    async def get(self, synthesis_id: str) -> Synthesis | None:
        result = await self.session.execute(
            select(Synthesis).where(Synthesis.id == synthesis_id)
        )
        return result.scalars().first()

    async def list(self, project_id: str, skip: int = 0, limit: int = 20) -> list[Synthesis]:
        stmt = (
            select(Synthesis)
            .where(Synthesis.project_id == project_id)
            .order_by(Synthesis.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_outline(self, synthesis_id: str, outline: list[dict]) -> Synthesis | None:
        synthesis = await self.get(synthesis_id)
        if not synthesis:
            return None
        synthesis.outline = outline
        synthesis.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(synthesis)
        return synthesis

    async def update_status(
        self,
        synthesis_id: str,
        status: str,
        content: str | None = None,
        outline: list[dict] | None = None,
        outline_approved: bool | None = None,
        error_message: str | None = None,
    ) -> Synthesis | None:
        synthesis = await self.get(synthesis_id)
        if not synthesis:
            return None
        synthesis.status = status
        synthesis.updated_at = datetime.utcnow()
        if content is not None:
            synthesis.content = content
        if outline is not None:
            synthesis.outline = outline
        if outline_approved is not None:
            synthesis.outline_approved = outline_approved
        if error_message is not None:
            synthesis.error_message = error_message
        await self.session.commit()
        await self.session.refresh(synthesis)
        return synthesis
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/synthesis_repository.py
git commit -m "feat: add synthesis repository"
```

---

## Task 3: Synthesis Service

**Files:**
- Create: `backend/app/services/synthesis_service.py`
- Create: `backend/tests/test_synthesis_service.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_synthesis_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.synthesis_service import SynthesisService

MOCK_CHUNKS = [
    {"id": f"chunk-{i}", "text": f"Chunk text about topic {i % 3}", "document_id": f"doc-{i}", "title": f"Doc{i}.md", "project_id": "proj-1"}
    for i in range(5)
]


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.embed = AsyncMock(return_value=[[0.1] * 3072])
    return llm


@pytest.fixture
def mock_qdrant():
    qdrant = AsyncMock()
    qdrant.search_by_filter.return_value = MOCK_CHUNKS
    qdrant.search.return_value = [
        {"id": c["id"], "score": 0.9, "payload": c}
        for c in MOCK_CHUNKS
    ]
    return qdrant


@pytest.fixture
def mock_contradiction_repo():
    repo = AsyncMock()
    repo.count.return_value = 0
    repo.list.return_value = []
    return repo


@pytest.fixture
def mock_synthesis_repo():
    repo = AsyncMock()
    synthesis = MagicMock()
    synthesis.id = "synth-1"
    synthesis.outline = [{"title": "Origins", "description": "How the world began"}]
    synthesis.outline_approved = True
    synthesis.status = "generating"
    repo.get.return_value = synthesis
    repo.update_status.return_value = synthesis
    return repo


@pytest.fixture
def service(mock_llm, mock_qdrant, mock_contradiction_repo, mock_synthesis_repo):
    return SynthesisService(
        llm_service=mock_llm,
        qdrant_service=mock_qdrant,
        contradiction_repo=mock_contradiction_repo,
        synthesis_repo=mock_synthesis_repo,
    )


@pytest.mark.asyncio
async def test_gate_check_blocks_with_open_contradictions(service, mock_contradiction_repo):
    mock_contradiction_repo.count.return_value = 3
    with pytest.raises(ValueError, match="Resolve all open contradictions"):
        await service.check_gate("proj-1")


@pytest.mark.asyncio
async def test_gate_check_passes_with_no_open_contradictions(service, mock_contradiction_repo):
    mock_contradiction_repo.count.return_value = 0
    await service.check_gate("proj-1")  # Should not raise


@pytest.mark.asyncio
async def test_generate_outline_returns_sections(service, mock_llm):
    mock_llm.generate.side_effect = [
        "Cosmogony, Characters, Factions, Events",  # batch topic extraction
        '[{"title": "Cosmogony", "description": "Origin of the world"}, {"title": "Characters", "description": "Key figures"}]',  # consolidation
    ]
    outline = await service.generate_outline("proj-1")
    assert len(outline) == 2
    assert outline[0]["title"] == "Cosmogony"


@pytest.mark.asyncio
async def test_generate_outline_handles_markdown_json(service, mock_llm):
    mock_llm.generate.side_effect = [
        "Topics: Cosmogony, Characters",
        '```json\n[{"title": "Cosmogony", "description": "Origins"}]\n```',
    ]
    outline = await service.generate_outline("proj-1")
    assert len(outline) == 1


@pytest.mark.asyncio
async def test_generate_section_includes_resolution_notes(service, mock_llm, mock_contradiction_repo):
    resolved = MagicMock()
    resolved.resolution_note = "Version 2 is canon"
    resolved.chunk_a_text = "old fact"
    resolved.chunk_b_text = "new fact"
    mock_contradiction_repo.list.return_value = [resolved]
    mock_llm.generate.return_value = "The world began with..."

    result = await service.generate_section(
        project_id="proj-1",
        section={"title": "Origins", "description": "How it began"},
    )
    assert result == "The world began with..."
    # Verify the prompt included the resolution note
    call_args = mock_llm.generate.call_args
    assert "Version 2 is canon" in call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")


@pytest.mark.asyncio
async def test_generate_section_works_without_resolution_notes(service, mock_llm, mock_contradiction_repo):
    mock_contradiction_repo.list.return_value = []
    mock_llm.generate.return_value = "The factions are..."

    result = await service.generate_section(
        project_id="proj-1",
        section={"title": "Factions", "description": "Major groups"},
    )
    assert result == "The factions are..."


@pytest.mark.asyncio
async def test_assemble_document(service):
    sections = [
        {"title": "Origins", "content": "The world began..."},
        {"title": "Characters", "content": "The heroes are..."},
    ]
    doc = service.assemble_document(sections)
    assert "# Origins" in doc
    assert "# Characters" in doc
    assert "The world began..." in doc
    assert "The heroes are..." in doc
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/test_synthesis_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.synthesis_service'`

- [ ] **Step 3: Write the SynthesisService**

Create `backend/app/services/synthesis_service.py`:

```python
import json
import logging
import re

from app.models.contradiction_repository import ContradictionRepository
from app.models.synthesis_repository import SynthesisRepository
from app.services.llm.service import LLMService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

TOPIC_EXTRACTION_PROMPT = """You are analyzing passages from a worldbuilding canon. Given the following passages, list the major topics covered. Return only a comma-separated list of topic names (e.g., "Cosmogony, Major Characters, Factions, Key Events, Geography").

Passages:
{chunks_text}

Topics:"""

OUTLINE_CONSOLIDATION_PROMPT = """You are organizing topics for a worldbuilding primer document. Given these topic lists extracted from different sections of a canon:

{topic_lists}

Consolidate them into a final ordered outline of 8-15 sections for a comprehensive world primer. Each section should have a title and a one-line description of what it covers.

Return JSON only — an array of objects: [{{"title": "Section Title", "description": "What this section covers"}}]"""

SECTION_GENERATION_PROMPT = """You are writing a section of a worldbuilding primer for newcomers. Write a flowing, engaging narrative about "{title}" ({description}) for someone being introduced to this world for the first time.

Use only the provided source material. Do not invent facts.

{resolution_notes_block}

Source material:
{source_chunks}

Write the section now. Do not include a heading — just the narrative text."""

CHUNKS_PER_BATCH = 50
SECTION_TOP_K = 30


class SynthesisService:
    def __init__(
        self,
        llm_service: LLMService,
        qdrant_service: QdrantService,
        contradiction_repo: ContradictionRepository,
        synthesis_repo: SynthesisRepository,
    ):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.contradiction_repo = contradiction_repo
        self.synthesis_repo = synthesis_repo

    async def check_gate(self, project_id: str) -> None:
        """Raise ValueError if open contradictions exist."""
        count = await self.contradiction_repo.count(project_id, status="open")
        if count > 0:
            raise ValueError(f"Resolve all open contradictions before generating ({count} remaining)")

    async def generate_outline(self, project_id: str) -> list[dict]:
        """Analyze all project chunks and generate a section outline."""
        all_chunks = await self.qdrant_service.search_by_filter(
            filters={"project_id": project_id},
            limit=10000,
        )
        if not all_chunks:
            raise ValueError("No documents found in this project")

        # Batch chunks and extract topics from each batch
        topic_lists = []
        for i in range(0, len(all_chunks), CHUNKS_PER_BATCH):
            batch = all_chunks[i : i + CHUNKS_PER_BATCH]
            chunks_text = "\n\n---\n\n".join(c["text"] for c in batch)
            topics = await self.llm_service.generate(
                prompt=TOPIC_EXTRACTION_PROMPT.format(chunks_text=chunks_text),
                temperature=0.3,
                max_tokens=512,
            )
            topic_lists.append(topics.strip())

        # Consolidate into final outline
        combined_topics = "\n".join(f"- {t}" for t in topic_lists)
        outline_json = await self.llm_service.generate(
            prompt=OUTLINE_CONSOLIDATION_PROMPT.format(topic_lists=combined_topics),
            temperature=0.3,
            max_tokens=2048,
        )

        return self._parse_outline_json(outline_json)

    def _parse_outline_json(self, response: str) -> list[dict]:
        """Parse outline JSON from LLM response, handling markdown wrapping."""
        text = response.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        try:
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("Outline must be a JSON array")
            return [
                {"title": str(item.get("title", "")), "description": str(item.get("description", ""))}
                for item in data
                if item.get("title")
            ]
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse outline JSON: %s", response[:300])
            raise ValueError("Failed to generate outline — LLM returned invalid JSON")

    async def generate_section(self, project_id: str, section: dict) -> str:
        """Generate a single section using relevant chunks and resolution notes."""
        # Find relevant chunks via semantic search
        query_text = f"{section['title']}: {section['description']}"
        query_vector = await self.llm_service.embed([query_text])
        similar = await self.qdrant_service.search(
            query_vector=query_vector[0],
            top_k=SECTION_TOP_K,
            filters={"project_id": project_id},
        )

        source_chunks = "\n\n---\n\n".join(
            m["payload"]["text"] for m in similar if m["payload"].get("text")
        )

        # Get resolution notes from resolved contradictions
        resolution_notes_block = ""
        resolved = await self.contradiction_repo.list(project_id, status="resolved", skip=0, limit=1000)
        notes = [c for c in resolved if c.resolution_note]
        if notes:
            note_lines = []
            for c in notes:
                note_lines.append(f"- Conflict: \"{c.chunk_a_text[:100]}...\" vs \"{c.chunk_b_text[:100]}...\" → Resolution: {c.resolution_note}")
            resolution_notes_block = "Where sources were contradictory, these resolution notes indicate which version is canon:\n" + "\n".join(note_lines)

        content = await self.llm_service.generate(
            prompt=SECTION_GENERATION_PROMPT.format(
                title=section["title"],
                description=section["description"],
                resolution_notes_block=resolution_notes_block,
                source_chunks=source_chunks,
            ),
            temperature=0.7,
            max_tokens=4096,
        )
        return content.strip()

    def assemble_document(self, sections: list[dict]) -> str:
        """Assemble generated sections into a final markdown document."""
        parts = []
        for section in sections:
            parts.append(f"# {section['title']}\n\n{section['content']}")
        return "\n\n---\n\n".join(parts)

    async def run_outline_generation(self, synthesis_id: str, project_id: str, auto: bool = False) -> None:
        """Background task: generate outline, optionally auto-approve and continue to sections."""
        try:
            outline = await self.generate_outline(project_id)
            if auto:
                await self.synthesis_repo.update_status(
                    synthesis_id, "generating", outline=outline, outline_approved=True
                )
                await self.run_section_generation(synthesis_id, project_id)
            else:
                await self.synthesis_repo.update_status(
                    synthesis_id, "outline_ready", outline=outline
                )
        except Exception as e:
            logger.exception("Outline generation failed for synthesis %s", synthesis_id)
            await self.synthesis_repo.update_status(
                synthesis_id, "failed", error_message=str(e)
            )

    async def run_section_generation(self, synthesis_id: str, project_id: str) -> None:
        """Background task: generate all sections and assemble the document."""
        try:
            synthesis = await self.synthesis_repo.get(synthesis_id)
            if not synthesis or not synthesis.outline:
                raise ValueError("Synthesis or outline not found")

            await self.synthesis_repo.update_status(synthesis_id, "generating")

            generated_sections = []
            for section in synthesis.outline:
                content = await self.generate_section(project_id, section)
                generated_sections.append({"title": section["title"], "content": content})

            document = self.assemble_document(generated_sections)
            await self.synthesis_repo.update_status(
                synthesis_id, "completed", content=document
            )
            logger.info("Synthesis %s completed: %d sections", synthesis_id, len(generated_sections))
        except Exception as e:
            logger.exception("Section generation failed for synthesis %s", synthesis_id)
            await self.synthesis_repo.update_status(
                synthesis_id, "failed", error_message=str(e)
            )
```

- [ ] **Step 4: Run tests**

```bash
cd backend && uv run pytest tests/test_synthesis_service.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/synthesis_service.py backend/tests/test_synthesis_service.py
git commit -m "feat: add synthesis service with outline generation and section assembly"
```

---

## Task 4: API Endpoints

**Files:**
- Create: `backend/app/api/v1/synthesis.py`
- Create: `backend/tests/test_synthesis_api.py`
- Modify: `backend/app/dependencies.py`
- Modify: `backend/app/api/v1/__init__.py`

- [ ] **Step 1: Add get_synthesis_service to dependencies.py**

Read `backend/app/dependencies.py`. Add after the `get_contradiction_service` function:

```python
from app.models.synthesis_repository import SynthesisRepository
from app.services.synthesis_service import SynthesisService


async def get_synthesis_service(
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> SynthesisService:
    contradiction_repo = ContradictionRepository(db)
    synthesis_repo = SynthesisRepository(db)
    return SynthesisService(
        llm_service=llm_service,
        qdrant_service=qdrant_service,
        contradiction_repo=contradiction_repo,
        synthesis_repo=synthesis_repo,
    )
```

Ensure `ContradictionRepository` is imported (it may already be imported for `get_contradiction_service`).

- [ ] **Step 2: Create the API routes**

Create `backend/app/api/v1/synthesis.py`:

```python
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, async_session
from app.models.project_repository import ProjectRepository
from app.models.contradiction_repository import ContradictionRepository
from app.models.synthesis_repository import SynthesisRepository
from app.dependencies import get_synthesis_service, get_llm_service, get_qdrant_service
from app.services.synthesis_service import SynthesisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/synthesis", tags=["synthesis"])


async def _verify_project(project_id: str, db: AsyncSession):
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _serialize(s) -> dict:
    return {
        "id": s.id,
        "project_id": s.project_id,
        "title": s.title,
        "outline": s.outline,
        "outline_approved": s.outline_approved,
        "content": s.content,
        "status": s.status,
        "error_message": s.error_message,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.post("", status_code=202)
async def create_synthesis(
    project_id: str,
    auto: bool = False,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)

    # Gate check: no open contradictions
    contradiction_repo = ContradictionRepository(db)
    open_count = await contradiction_repo.count(project_id, status="open")
    if open_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Resolve all open contradictions before generating a synthesis ({open_count} remaining)",
        )

    synthesis_repo = SynthesisRepository(db)
    synthesis = await synthesis_repo.create(project_id=project_id, auto=auto)

    llm_service = get_llm_service()
    qdrant_service = get_qdrant_service()

    async def _background():
        try:
            async with async_session() as session:
                c_repo = ContradictionRepository(session)
                s_repo = SynthesisRepository(session)
                svc = SynthesisService(
                    llm_service=llm_service,
                    qdrant_service=qdrant_service,
                    contradiction_repo=c_repo,
                    synthesis_repo=s_repo,
                )
                await svc.run_outline_generation(synthesis.id, project_id, auto=auto)
        except Exception:
            logger.exception("Background synthesis failed for %s", synthesis.id)

    asyncio.create_task(_background())
    return _serialize(synthesis)


@router.get("")
async def list_syntheses(
    project_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = SynthesisRepository(db)
    syntheses = await repo.list(project_id=project_id, skip=skip, limit=limit)
    return [_serialize(s) for s in syntheses]


@router.get("/{synthesis_id}")
async def get_synthesis(
    project_id: str,
    synthesis_id: str,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = SynthesisRepository(db)
    synthesis = await repo.get(synthesis_id)
    if not synthesis or synthesis.project_id != project_id:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    return _serialize(synthesis)


class OutlineUpdateBody(BaseModel):
    outline: list[dict]


@router.patch("/{synthesis_id}/outline")
async def update_outline(
    project_id: str,
    synthesis_id: str,
    body: OutlineUpdateBody,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = SynthesisRepository(db)
    synthesis = await repo.get(synthesis_id)
    if not synthesis or synthesis.project_id != project_id:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    if synthesis.status != "outline_ready" or synthesis.outline_approved:
        raise HTTPException(status_code=409, detail="Outline cannot be edited in current state")
    updated = await repo.update_outline(synthesis_id, body.outline)
    return _serialize(updated)


@router.post("/{synthesis_id}/approve", status_code=202)
async def approve_outline(
    project_id: str,
    synthesis_id: str,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = SynthesisRepository(db)
    synthesis = await repo.get(synthesis_id)
    if not synthesis or synthesis.project_id != project_id:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    if synthesis.status != "outline_ready":
        raise HTTPException(status_code=409, detail="Can only approve when status is outline_ready")

    await repo.update_status(synthesis_id, "generating", outline_approved=True)

    llm_service = get_llm_service()
    qdrant_service = get_qdrant_service()

    async def _background():
        try:
            async with async_session() as session:
                c_repo = ContradictionRepository(session)
                s_repo = SynthesisRepository(session)
                svc = SynthesisService(
                    llm_service=llm_service,
                    qdrant_service=qdrant_service,
                    contradiction_repo=c_repo,
                    synthesis_repo=s_repo,
                )
                await svc.run_section_generation(synthesis.id, project_id)
        except Exception:
            logger.exception("Background section generation failed for %s", synthesis.id)

    asyncio.create_task(_background())
    return {"id": synthesis.id, "status": "generating"}


@router.get("/{synthesis_id}/download")
async def download_synthesis(
    project_id: str,
    synthesis_id: str,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = SynthesisRepository(db)
    synthesis = await repo.get(synthesis_id)
    if not synthesis or synthesis.project_id != project_id:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    if synthesis.status != "completed" or not synthesis.content:
        raise HTTPException(status_code=409, detail="Synthesis is not yet complete")

    filename = f"{synthesis.title.replace(' ', '_')}.md"
    return PlainTextResponse(
        content=synthesis.content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 3: Register the router**

In `backend/app/api/v1/__init__.py`, add:

```python
from app.api.v1.synthesis import router as synthesis_router
```

And add to the router registration:

```python
router.include_router(synthesis_router)
```

- [ ] **Step 4: Write API tests**

Create `backend/tests/test_synthesis_api.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app


@pytest.fixture
def sample_synthesis():
    s = MagicMock()
    s.id = "synth-1"
    s.project_id = "proj-1"
    s.title = "World Primer"
    s.outline = [{"title": "Origins", "description": "How it began"}]
    s.outline_approved = False
    s.content = None
    s.status = "outline_ready"
    s.error_message = None
    s.created_at = datetime(2026, 4, 5, tzinfo=timezone.utc)
    s.updated_at = datetime(2026, 4, 5, tzinfo=timezone.utc)
    return s


@pytest.mark.asyncio
async def test_create_synthesis_blocked_by_contradictions():
    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.ContradictionRepository") as MockCRepo:
        mock_c_repo = AsyncMock()
        mock_c_repo.count.return_value = 5
        MockCRepo.return_value = mock_c_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/projects/proj-1/synthesis")

        assert resp.status_code == 400
        assert "contradictions" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_synthesis_succeeds(sample_synthesis):
    sample_synthesis.status = "outline_pending"
    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.ContradictionRepository") as MockCRepo, \
         patch("app.api.v1.synthesis.SynthesisRepository") as MockSRepo, \
         patch("app.api.v1.synthesis.asyncio.create_task"):
        mock_c_repo = AsyncMock()
        mock_c_repo.count.return_value = 0
        MockCRepo.return_value = mock_c_repo
        mock_s_repo = AsyncMock()
        mock_s_repo.create.return_value = sample_synthesis
        MockSRepo.return_value = mock_s_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/projects/proj-1/synthesis")

        assert resp.status_code == 202
        assert resp.json()["id"] == "synth-1"


@pytest.mark.asyncio
async def test_get_synthesis(sample_synthesis):
    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.SynthesisRepository") as MockSRepo:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = sample_synthesis
        MockSRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/proj-1/synthesis/synth-1")

        assert resp.status_code == 200
        assert resp.json()["status"] == "outline_ready"


@pytest.mark.asyncio
async def test_update_outline(sample_synthesis):
    updated = MagicMock()
    updated.id = "synth-1"
    updated.project_id = "proj-1"
    updated.title = "World Primer"
    updated.outline = [{"title": "New Section", "description": "Updated"}]
    updated.outline_approved = False
    updated.content = None
    updated.status = "outline_ready"
    updated.error_message = None
    updated.created_at = datetime(2026, 4, 5, tzinfo=timezone.utc)
    updated.updated_at = datetime(2026, 4, 5, tzinfo=timezone.utc)

    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.SynthesisRepository") as MockSRepo:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = sample_synthesis
        mock_repo.update_outline.return_value = updated
        MockSRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(
                "/api/v1/projects/proj-1/synthesis/synth-1/outline",
                json={"outline": [{"title": "New Section", "description": "Updated"}]},
            )

        assert resp.status_code == 200
        assert resp.json()["outline"][0]["title"] == "New Section"


@pytest.mark.asyncio
async def test_update_outline_rejected_after_approval(sample_synthesis):
    sample_synthesis.outline_approved = True
    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.SynthesisRepository") as MockSRepo:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = sample_synthesis
        MockSRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(
                "/api/v1/projects/proj-1/synthesis/synth-1/outline",
                json={"outline": [{"title": "X", "description": "Y"}]},
            )

        assert resp.status_code == 409


@pytest.mark.asyncio
async def test_approve_rejected_wrong_status(sample_synthesis):
    sample_synthesis.status = "generating"
    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.SynthesisRepository") as MockSRepo:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = sample_synthesis
        MockSRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/projects/proj-1/synthesis/synth-1/approve")

        assert resp.status_code == 409


@pytest.mark.asyncio
async def test_download_completed(sample_synthesis):
    sample_synthesis.status = "completed"
    sample_synthesis.content = "# Origins\n\nThe world began..."
    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.SynthesisRepository") as MockSRepo:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = sample_synthesis
        MockSRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/proj-1/synthesis/synth-1/download")

        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert "# Origins" in resp.text


@pytest.mark.asyncio
async def test_download_rejected_incomplete(sample_synthesis):
    with patch("app.api.v1.synthesis._verify_project", new_callable=AsyncMock), \
         patch("app.api.v1.synthesis.SynthesisRepository") as MockSRepo:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = sample_synthesis
        MockSRepo.return_value = mock_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/proj-1/synthesis/synth-1/download")

        assert resp.status_code == 409
```

- [ ] **Step 5: Run all tests**

```bash
cd backend && uv run pytest tests/test_synthesis_service.py tests/test_synthesis_api.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/synthesis.py backend/app/api/v1/__init__.py backend/app/dependencies.py backend/tests/test_synthesis_api.py
git commit -m "feat: add synthesis API endpoints (create, list, get, outline, approve, download)"
```

---

## Task 5: Frontend API Client & Hooks

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/useSynthesis.ts`

- [ ] **Step 1: Add synthesis types and API methods**

Add interfaces to `frontend/src/lib/api.ts` after the `ContradictionList` interface:

```typescript
export interface SynthesisOutlineSection {
  title: string;
  description: string;
}

export interface Synthesis {
  id: string;
  project_id: string;
  title: string;
  outline: SynthesisOutlineSection[] | null;
  outline_approved: boolean;
  content: string | null;
  status: "outline_pending" | "outline_ready" | "generating" | "completed" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
}
```

Add the `synthesis` namespace to the `api` object:

```typescript
  synthesis: {
    list: (projectId: string) =>
      request<Synthesis[]>(`/api/v1/projects/${projectId}/synthesis`),
    get: (projectId: string, id: string) =>
      request<Synthesis>(`/api/v1/projects/${projectId}/synthesis/${id}`),
    create: (projectId: string, auto = false) =>
      request<Synthesis>(
        `/api/v1/projects/${projectId}/synthesis?auto=${auto}`,
        { method: "POST" }
      ),
    updateOutline: (projectId: string, id: string, outline: SynthesisOutlineSection[]) =>
      request<Synthesis>(
        `/api/v1/projects/${projectId}/synthesis/${id}/outline`,
        { method: "PATCH", body: JSON.stringify({ outline }) }
      ),
    approve: (projectId: string, id: string) =>
      request<{ id: string; status: string }>(
        `/api/v1/projects/${projectId}/synthesis/${id}/approve`,
        { method: "POST" }
      ),
    download: (projectId: string, id: string) =>
      `/api/v1/projects/${projectId}/synthesis/${id}/download`,
  },
```

Note: `download` returns a URL string (not a fetch) — the page will use `window.open()` or an `<a>` tag.

- [ ] **Step 2: Create the hooks**

Read `frontend/src/hooks/useContradictions.ts` to see the pattern with `useActiveProject`. Then create `frontend/src/hooks/useSynthesis.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useActiveProject } from "@/contexts/ProjectContext";
import type { SynthesisOutlineSection } from "@/lib/api";

export function useSyntheses() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  return useQuery({
    queryKey: ["syntheses", projectId],
    queryFn: () => api.synthesis.list(projectId!),
    enabled: !!projectId,
  });
}

export function useSynthesis(id: string | null) {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  return useQuery({
    queryKey: ["synthesis", projectId, id],
    queryFn: () => api.synthesis.get(projectId!, id!),
    enabled: !!projectId && !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "outline_pending" || status === "generating") {
        return 5000;
      }
      return false;
    },
  });
}

export function useCreateSynthesis() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (auto: boolean = false) => api.synthesis.create(projectId!, auto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["syntheses", projectId] });
    },
  });
}

export function useUpdateOutline() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, outline }: { id: string; outline: SynthesisOutlineSection[] }) =>
      api.synthesis.updateOutline(projectId!, id, outline),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["synthesis", projectId, vars.id] });
    },
  });
}

export function useApproveSynthesis() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.synthesis.approve(projectId!, id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["synthesis", projectId, id] });
    },
  });
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/hooks/useSynthesis.ts
git commit -m "feat: add synthesis API client and React Query hooks with polling"
```

---

## Task 6: Install react-markdown

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install dependencies**

```bash
cd frontend && npm install react-markdown remark-gfm
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add react-markdown and remark-gfm"
```

---

## Task 7: Frontend Synthesis Page

**Files:**
- Create: `frontend/src/components/synthesis/OutlineEditor.tsx`
- Create: `frontend/src/components/synthesis/SynthesisViewer.tsx`
- Create: `frontend/src/pages/SynthesisPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create the OutlineEditor component**

Create `frontend/src/components/synthesis/OutlineEditor.tsx`:

```tsx
import { useState } from "react";
import { Button } from "../ui/button";
import type { SynthesisOutlineSection } from "../../lib/api";

interface OutlineEditorProps {
  outline: SynthesisOutlineSection[];
  readOnly?: boolean;
  onSave: (outline: SynthesisOutlineSection[]) => void;
  onApprove: () => void;
}

export function OutlineEditor({ outline, readOnly, onSave, onApprove }: OutlineEditorProps) {
  const [sections, setSections] = useState(outline);

  const updateSection = (index: number, field: "title" | "description", value: string) => {
    const updated = [...sections];
    updated[index] = { ...updated[index], [field]: value };
    setSections(updated);
  };

  const removeSection = (index: number) => {
    setSections(sections.filter((_, i) => i !== index));
  };

  const moveSection = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= sections.length) return;
    const updated = [...sections];
    [updated[index], updated[target]] = [updated[target], updated[index]];
    setSections(updated);
  };

  return (
    <div className="space-y-3">
      {sections.map((section, i) => (
        <div key={i} className="flex gap-2 items-start border rounded p-3">
          {!readOnly && (
            <div className="flex flex-col gap-1">
              <Button size="sm" variant="ghost" onClick={() => moveSection(i, -1)} disabled={i === 0}>
                ↑
              </Button>
              <Button size="sm" variant="ghost" onClick={() => moveSection(i, 1)} disabled={i === sections.length - 1}>
                ↓
              </Button>
            </div>
          )}
          <div className="flex-1 space-y-1">
            {readOnly ? (
              <>
                <p className="font-medium">{section.title}</p>
                <p className="text-sm text-muted-foreground">{section.description}</p>
              </>
            ) : (
              <>
                <input
                  className="w-full rounded border border-input bg-background px-3 py-1 text-sm font-medium"
                  value={section.title}
                  onChange={(e) => updateSection(i, "title", e.target.value)}
                />
                <input
                  className="w-full rounded border border-input bg-background px-3 py-1 text-sm text-muted-foreground"
                  value={section.description}
                  onChange={(e) => updateSection(i, "description", e.target.value)}
                />
              </>
            )}
          </div>
          {!readOnly && (
            <Button size="sm" variant="ghost" onClick={() => removeSection(i)}>
              ✕
            </Button>
          )}
        </div>
      ))}
      {!readOnly && (
        <div className="flex gap-2 pt-2">
          <Button size="sm" variant="outline" onClick={() => onSave(sections)}>
            Save Changes
          </Button>
          <Button size="sm" onClick={onApprove}>
            Approve & Generate
          </Button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create the SynthesisViewer component**

Create `frontend/src/components/synthesis/SynthesisViewer.tsx`:

```tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "../ui/button";
import { api } from "../../lib/api";
import { useActiveProject } from "../../contexts/ProjectContext";

interface SynthesisViewerProps {
  synthesisId: string;
  title: string;
  content: string;
  onRegenerate: () => void;
}

export function SynthesisViewer({ synthesisId, title, content, onRegenerate }: SynthesisViewerProps) {
  const { activeProject } = useActiveProject();

  const handleDownload = () => {
    if (!activeProject) return;
    window.open(api.synthesis.download(activeProject.id, synthesisId), "_blank");
  };

  return (
    <div>
      <div className="flex gap-2 mb-6">
        <Button size="sm" onClick={handleDownload}>
          Download .md
        </Button>
        <Button size="sm" variant="outline" onClick={onRegenerate}>
          Regenerate
        </Button>
      </div>
      <article className="prose prose-sm max-w-none dark:prose-invert">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </article>
    </div>
  );
}
```

- [ ] **Step 3: Create the SynthesisPage**

Create `frontend/src/pages/SynthesisPage.tsx`:

```tsx
import { useState } from "react";
import { Button } from "../components/ui/button";
import { OutlineEditor } from "../components/synthesis/OutlineEditor";
import { SynthesisViewer } from "../components/synthesis/SynthesisViewer";
import {
  useSyntheses,
  useSynthesis,
  useCreateSynthesis,
  useUpdateOutline,
  useApproveSynthesis,
} from "../hooks/useSynthesis";
import { useContradictions } from "../hooks/useContradictions";
import { useActiveProject } from "../contexts/ProjectContext";
import { toast } from "sonner";

export function SynthesisPage() {
  const { activeProject } = useActiveProject();
  const { data: syntheses } = useSyntheses();
  const { data: contradictions } = useContradictions("open");
  const create = useCreateSynthesis();
  const updateOutline = useUpdateOutline();
  const approve = useApproveSynthesis();

  const [activeSynthesisId, setActiveSynthesisId] = useState<string | null>(null);
  const { data: activeSynthesis } = useSynthesis(activeSynthesisId);

  // Auto-select the most recent synthesis
  const current = activeSynthesis || (syntheses?.[0] ?? null);
  const currentId = current?.id ?? null;

  // Keep activeSynthesisId in sync
  if (currentId && currentId !== activeSynthesisId) {
    setActiveSynthesisId(currentId);
  }

  const openCount = contradictions?.total ?? 0;
  const gateBlocked = openCount > 0;

  if (!activeProject) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Synthesis</h1>
        <p className="text-muted-foreground">Select a project first.</p>
      </div>
    );
  }

  const handleCreate = (auto: boolean) => {
    create.mutate(auto, {
      onSuccess: (data) => {
        setActiveSynthesisId(data.id);
        toast.info(auto ? "Generating world primer..." : "Generating outline...");
      },
      onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to start synthesis"),
    });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Synthesis</h1>
        <div className="flex gap-2">
          <Button onClick={() => handleCreate(false)} disabled={gateBlocked || create.isPending}>
            Generate World Primer
          </Button>
          <Button variant="outline" onClick={() => handleCreate(true)} disabled={gateBlocked || create.isPending}>
            Quick Generate
          </Button>
        </div>
      </div>

      {gateBlocked && (
        <p className="text-sm text-destructive mb-6">
          Resolve all {openCount} open contradictions before generating.
        </p>
      )}

      {!current && !gateBlocked && (
        <p className="text-muted-foreground">No syntheses yet. Generate your first world primer above.</p>
      )}

      {current?.status === "outline_pending" && (
        <p className="text-muted-foreground">Generating outline...</p>
      )}

      {current?.status === "outline_ready" && current.outline && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Review Outline</h2>
          <OutlineEditor
            outline={current.outline}
            onSave={(outline) => updateOutline.mutate({ id: current.id, outline })}
            onApprove={() => approve.mutate(current.id, {
              onSuccess: () => toast.info("Generating sections..."),
            })}
          />
        </div>
      )}

      {current?.status === "generating" && (
        <div>
          <p className="text-muted-foreground mb-4">Generating sections...</p>
          {current.outline && <OutlineEditor outline={current.outline} readOnly onSave={() => {}} onApprove={() => {}} />}
        </div>
      )}

      {current?.status === "completed" && current.content && (
        <SynthesisViewer
          synthesisId={current.id}
          title={current.title}
          content={current.content}
          onRegenerate={() => handleCreate(false)}
        />
      )}

      {current?.status === "failed" && (
        <div>
          <p className="text-destructive mb-4">Generation failed: {current.error_message}</p>
          <Button onClick={() => handleCreate(false)}>Retry</Button>
        </div>
      )}

      {syntheses && syntheses.length > 1 && (
        <div className="mt-8 border-t pt-6">
          <h2 className="text-lg font-semibold mb-3">Previous Syntheses</h2>
          <div className="space-y-2">
            {syntheses.map((s) => (
              <button
                key={s.id}
                className={`block w-full text-left rounded p-2 text-sm hover:bg-muted ${s.id === currentId ? "bg-muted font-medium" : ""}`}
                onClick={() => setActiveSynthesisId(s.id)}
              >
                {s.title} — {s.status} — {new Date(s.created_at).toLocaleDateString()}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default SynthesisPage;
```

- [ ] **Step 4: Add the route**

In `frontend/src/App.tsx`, add the import:

```typescript
import SynthesisPage from "./pages/SynthesisPage";
```

Add the route inside the Shell layout, after the contradictions route:

```tsx
<Route path="/synthesis" element={<SynthesisPage />} />
```

- [ ] **Step 5: Add the sidebar link**

In `frontend/src/components/layout/Sidebar.tsx`, add to the `links` array after Contradictions:

```typescript
{ to: "/synthesis", label: "Synthesis", icon: "\uD83D\uDCD6" },
```

(Unicode for the open book emoji)

- [ ] **Step 6: Verify build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/synthesis/ frontend/src/pages/SynthesisPage.tsx frontend/src/App.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "feat: add synthesis page with outline editor, markdown viewer, and download"
```

---

## Task 8: End-to-End Verification

**Files:** None (testing only)

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && uv run pytest tests/ -v --ignore=tests/test_integration.py
```

Expected: All tests PASS (existing + new).

- [ ] **Step 2: Rebuild Docker**

```bash
cd D:/MajorProjects/CURRENT/worldforge && docker compose up -d --build
```

Wait for healthy:

```bash
docker compose ps
```

- [ ] **Step 3: Verify API endpoints**

```bash
# List syntheses (should be empty)
curl -s http://localhost:8080/api/v1/projects/b568b15e-64db-408c-a408-65bf71948050/synthesis

# Try creating (may fail if open contradictions exist — that's the gate working)
curl -s -X POST "http://localhost:8080/api/v1/projects/b568b15e-64db-408c-a408-65bf71948050/synthesis?auto=false"
```

- [ ] **Step 4: Verify the UI**

Open http://localhost:8080/synthesis in the browser. Verify:
- Synthesis page loads
- Sidebar shows the Synthesis link
- If open contradictions exist, the Generate button is disabled with the count message
- If no open contradictions, clicking Generate starts outline generation
