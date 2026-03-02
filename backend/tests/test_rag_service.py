"""Tests for RAGService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.rag_service import RAGService


@pytest.fixture
def llm_service():
    svc = AsyncMock()
    svc.embed.return_value = [[0.1, 0.2, 0.3]]
    svc.generate.return_value = "The capital of Eldoria is Sunspire."
    return svc


@pytest.fixture
def qdrant_service():
    return AsyncMock()


@pytest.fixture
def rag_service(llm_service, qdrant_service):
    return RAGService(llm_service=llm_service, qdrant_service=qdrant_service)


@pytest.mark.asyncio
async def test_rag_query_returns_answer_with_citations(rag_service, llm_service, qdrant_service):
    """Mock embed, search (one result), generate. Verify answer, citations, and calls."""
    qdrant_service.search.return_value = [
        {
            "id": "point-1",
            "score": 0.92,
            "payload": {
                "text": "The capital of Eldoria is Sunspire, a city of golden towers.",
                "document_id": "doc-abc",
                "title": "Geography of Eldoria",
                "chunk_index": 3,
            },
        }
    ]

    result = await rag_service.query("What is the capital of Eldoria?")

    assert result["answer"] == "The capital of Eldoria is Sunspire."
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document_id"] == "doc-abc"
    assert result["citations"][0]["title"] == "Geography of Eldoria"
    assert result["citations"][0]["relevance_score"] == 0.92
    assert "processing_time_ms" in result

    llm_service.embed.assert_awaited_once()
    qdrant_service.search.assert_awaited_once()
    llm_service.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_rag_query_no_results(rag_service, llm_service, qdrant_service):
    """When search returns nothing, generate is still called and citations is empty."""
    qdrant_service.search.return_value = []
    llm_service.generate.return_value = "I couldn't find relevant information in the canon."

    result = await rag_service.query("What is the population of Zarathia?")

    assert result["citations"] == []
    assert "couldn't find" in result["answer"]
    assert "processing_time_ms" in result

    llm_service.generate.assert_awaited_once()
