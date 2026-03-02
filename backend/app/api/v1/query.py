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
