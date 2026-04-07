from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import get_db
from app.models.repositories import DocumentRepository
from app.models.contradiction_repository import ContradictionRepository
from app.services.llm import LLMService, AnthropicProvider, OpenAIProvider
from app.services.qdrant_service import QdrantService
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService
from app.services.contradiction_service import ContradictionService
from app.models.synthesis_repository import SynthesisRepository
from app.services.synthesis_service import SynthesisService

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


def reset_llm_service():
    global _llm_service
    _llm_service = None


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


async def get_contradiction_service(
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> ContradictionService:
    return ContradictionService(
        llm_service=llm_service,
        qdrant_service=qdrant_service,
        repo=ContradictionRepository(db),
    )


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
