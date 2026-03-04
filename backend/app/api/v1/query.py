from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.project_repository import ProjectRepository
from app.dependencies import get_rag_service

router = APIRouter(prefix="/projects/{project_id}/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=10, ge=1, le=50)


@router.post("")
async def query_canon(
    project_id: str,
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    rag_service=Depends(get_rag_service),
):
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await rag_service.query(
        question=request.question, top_k=request.top_k, project_id=project_id,
    )
    return result
