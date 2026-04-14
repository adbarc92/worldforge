from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.project_repository import ProjectRepository
from app.dependencies import get_qdrant_service

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


@router.post("")
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    project = await repo.create(name=body.name, description=body.description)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    projects = await repo.list()
    result = []
    for p in projects:
        doc_count = await repo.get_document_count(p.id)
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "document_count": doc_count,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        })
    return result


@router.get("/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    doc_count = await repo.get_document_count(project_id)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "document_count": doc_count,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


@router.put("/{project_id}")
async def update_project(project_id: str, body: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    project = await repo.update(project_id, name=body.name, description=body.description)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "updated_at": project.updated_at.isoformat(),
    }


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    qdrant = get_qdrant_service()
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await qdrant.delete_by_project(project_id)
    await repo.delete(project_id)
    return {"status": "deleted"}
