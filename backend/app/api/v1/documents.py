import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.repositories import DocumentRepository
from app.models.project_repository import ProjectRepository
from app.core.config import settings
from app.dependencies import get_ingestion_service

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

    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "project_id": project_id,
    }


@router.get("")
async def list_documents(
    project_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    await _verify_project(project_id, db)
    repo = DocumentRepository(db)
    docs = await repo.list(project_id=project_id, skip=skip, limit=limit)
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
async def get_document(project_id: str, doc_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_project(project_id, db)
    repo = DocumentRepository(db)
    doc = await repo.get(doc_id)
    if not doc or doc.project_id != project_id:
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
    project_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    ingestion_service=Depends(get_ingestion_service),
):
    await _verify_project(project_id, db)
    repo = DocumentRepository(db)
    doc = await repo.get(doc_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    deleted = await ingestion_service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}
