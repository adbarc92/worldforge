import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, async_session
from app.models.contradiction_repository import ContradictionRepository
from app.models.project_repository import ProjectRepository
from app.dependencies import get_contradiction_service, get_llm_service, get_qdrant_service
from app.services.contradiction_service import ContradictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/contradictions", tags=["contradictions"])


class ResolutionBody(BaseModel):
    note: str | None = None


async def _verify_project(project_id: str, db: AsyncSession):
    """Verify project exists, raise 404 if not."""
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("")
async def list_contradictions(
    project_id: str,
    status: str = "open",
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = ContradictionRepository(db)
    items = await repo.list(project_id=project_id, status=status, skip=skip, limit=limit)
    total = await repo.count(project_id=project_id, status=status)
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
                "resolution_note": c.resolution_note,
                "created_at": c.created_at.isoformat(),
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            }
            for c in items
        ],
        "total": total,
    }


@router.post("/scan", status_code=202)
async def scan_contradictions(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)

    # Capture singletons now; the background task will create its own db session
    llm_service = get_llm_service()
    qdrant_service = get_qdrant_service()

    async def _background_scan():
        try:
            async with async_session() as session:
                repo = ContradictionRepository(session)
                svc = ContradictionService(
                    llm_service=llm_service,
                    qdrant_service=qdrant_service,
                    repo=repo,
                )
                count = await svc.scan_project(project_id)
                logger.info("Background scan for project %s found %d contradictions", project_id, count)
        except Exception:
            logger.exception("Background contradiction scan failed for project %s", project_id)

    asyncio.create_task(_background_scan())
    return {"status": "scan_started", "project_id": project_id}


@router.patch("/{contradiction_id}/resolve")
async def resolve_contradiction(
    project_id: str,
    contradiction_id: str,
    body: ResolutionBody = ResolutionBody(),
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = ContradictionRepository(db)
    contradiction = await repo.update_status(contradiction_id, "resolved", resolution_note=body.note)
    if not contradiction:
        raise HTTPException(status_code=404, detail="Contradiction not found")
    return {"id": contradiction.id, "status": contradiction.status, "resolution_note": contradiction.resolution_note}


@router.patch("/{contradiction_id}/dismiss")
async def dismiss_contradiction(
    project_id: str,
    contradiction_id: str,
    body: ResolutionBody = ResolutionBody(),
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = ContradictionRepository(db)
    contradiction = await repo.update_status(contradiction_id, "dismissed", resolution_note=body.note)
    if not contradiction:
        raise HTTPException(status_code=404, detail="Contradiction not found")
    return {"id": contradiction.id, "status": contradiction.status, "resolution_note": contradiction.resolution_note}


@router.patch("/{contradiction_id}/reopen")
async def reopen_contradiction(
    project_id: str,
    contradiction_id: str,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = ContradictionRepository(db)
    contradiction = await repo.update_status(contradiction_id, "open")
    if not contradiction:
        raise HTTPException(status_code=404, detail="Contradiction not found")
    return {"id": contradiction.id, "status": contradiction.status}
