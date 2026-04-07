import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, async_session
from app.models.contradiction_repository import ContradictionRepository
from app.models.project_repository import ProjectRepository
from app.models.synthesis_repository import SynthesisRepository
from app.dependencies import get_synthesis_service, get_llm_service, get_qdrant_service
from app.services.synthesis_service import SynthesisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/synthesis", tags=["synthesis"])


class OutlineBody(BaseModel):
    outline: list[dict]


async def _verify_project(project_id: str, db: AsyncSession):
    """Verify project exists, raise 404 if not."""
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _serialize(s) -> dict:
    """Serialize a Synthesis ORM object to a dict."""
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

    # Gate: check for open contradictions
    contradiction_repo = ContradictionRepository(db)
    open_count = await contradiction_repo.count(project_id, status="open")
    if open_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot synthesize: {open_count} open contradictions must be resolved first",
        )

    # Create synthesis record
    synthesis_repo = SynthesisRepository(db)
    synthesis = await synthesis_repo.create(project_id=project_id, auto=auto)

    # Capture singletons for background task
    llm_service = get_llm_service()
    qdrant_service = get_qdrant_service()

    synthesis_id = synthesis.id

    async def _background_outline():
        try:
            async with async_session() as session:
                contradiction_repo_bg = ContradictionRepository(session)
                synthesis_repo_bg = SynthesisRepository(session)
                svc = SynthesisService(
                    llm_service=llm_service,
                    qdrant_service=qdrant_service,
                    contradiction_repo=contradiction_repo_bg,
                    synthesis_repo=synthesis_repo_bg,
                )
                await svc.run_outline_generation(synthesis_id, project_id, auto=auto)
                logger.info("Background outline generation completed for synthesis %s", synthesis_id)
        except Exception:
            logger.exception("Background outline generation failed for synthesis %s", synthesis_id)

    asyncio.create_task(_background_outline())
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
    items = await repo.list(project_id=project_id, skip=skip, limit=limit)
    return [_serialize(s) for s in items]


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


@router.patch("/{synthesis_id}/outline")
async def update_outline(
    project_id: str,
    synthesis_id: str,
    body: OutlineBody,
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
        raise HTTPException(status_code=409, detail="Outline can only be approved when status is outline_ready")

    # Mark outline as approved
    await repo.update_status(synthesis_id, status="outline_approved", outline_approved=True)

    # Capture singletons for background task
    llm_service = get_llm_service()
    qdrant_service = get_qdrant_service()

    async def _background_sections():
        try:
            async with async_session() as session:
                contradiction_repo_bg = ContradictionRepository(session)
                synthesis_repo_bg = SynthesisRepository(session)
                svc = SynthesisService(
                    llm_service=llm_service,
                    qdrant_service=qdrant_service,
                    contradiction_repo=contradiction_repo_bg,
                    synthesis_repo=synthesis_repo_bg,
                )
                await svc.run_section_generation(synthesis_id, project_id)
                logger.info("Background section generation completed for synthesis %s", synthesis_id)
        except Exception:
            logger.exception("Background section generation failed for synthesis %s", synthesis_id)

    asyncio.create_task(_background_sections())
    return {"status": "approved", "synthesis_id": synthesis_id}


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
    if synthesis.status != "completed":
        raise HTTPException(status_code=409, detail="Synthesis is not yet completed")

    filename = f"{synthesis.title.replace(' ', '_')}.md"
    return PlainTextResponse(
        content=synthesis.content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
