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
