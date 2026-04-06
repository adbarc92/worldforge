import pytest
from unittest.mock import AsyncMock, patch
from app.services.contradiction_service import ContradictionService


@pytest.fixture
def mock_llm_service():
    return AsyncMock()


@pytest.fixture
def mock_qdrant_service():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.pair_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def service(mock_llm_service, mock_qdrant_service, mock_repo):
    return ContradictionService(
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service,
        repo=mock_repo,
    )


@pytest.mark.asyncio
async def test_classify_contradiction_positive(service, mock_llm_service):
    mock_llm_service.generate.return_value = '{"is_contradiction": true, "explanation": "Chunk A says X, Chunk B says Y"}'
    result = await service.classify_pair("Passage A text", "Passage B text")
    assert result["is_contradiction"] is True
    assert "Chunk A says X" in result["explanation"]


@pytest.mark.asyncio
async def test_classify_contradiction_negative(service, mock_llm_service):
    mock_llm_service.generate.return_value = '{"is_contradiction": false, "explanation": "No conflict"}'
    result = await service.classify_pair("Passage A text", "Passage B text")
    assert result["is_contradiction"] is False


@pytest.mark.asyncio
async def test_classify_handles_markdown_wrapped_json(service, mock_llm_service):
    mock_llm_service.generate.return_value = '```json\n{"is_contradiction": true, "explanation": "conflict"}\n```'
    result = await service.classify_pair("A", "B")
    assert result["is_contradiction"] is True


@pytest.mark.asyncio
async def test_classify_handles_malformed_json(service, mock_llm_service):
    mock_llm_service.generate.return_value = "This is not JSON at all"
    result = await service.classify_pair("A", "B")
    assert result["is_contradiction"] is False


@pytest.mark.asyncio
async def test_scan_document_skips_same_document_chunks(service, mock_qdrant_service, mock_repo):
    mock_qdrant_service.search.return_value = [
        {"id": "other-chunk", "score": 0.9, "payload": {"document_id": "doc-1", "text": "similar text"}}
    ]
    with patch.object(service, "_get_document_chunks") as mock_get:
        mock_get.return_value = [
            {"id": "chunk-1", "text": "some text", "document_id": "doc-1", "title": "", "project_id": "proj-1"}
        ]
        await service.scan_document("doc-1", "proj-1")

    service.llm_service.generate.assert_not_called()
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_scan_document_skips_existing_pairs(service, mock_qdrant_service, mock_llm_service, mock_repo):
    mock_repo.pair_exists.return_value = True
    mock_qdrant_service.search.return_value = [
        {"id": "other-chunk", "score": 0.9, "payload": {"document_id": "doc-2", "text": "conflict text"}}
    ]
    with patch.object(service, "_get_document_chunks") as mock_get:
        mock_get.return_value = [
            {"id": "chunk-1", "text": "some text", "document_id": "doc-1", "title": "", "project_id": "proj-1"}
        ]
        await service.scan_document("doc-1", "proj-1")

    mock_llm_service.generate.assert_not_called()
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_scan_document_creates_contradiction(service, mock_qdrant_service, mock_llm_service, mock_repo):
    mock_llm_service.generate.return_value = '{"is_contradiction": true, "explanation": "They conflict"}'
    mock_qdrant_service.search.return_value = [
        {"id": "other-chunk", "score": 0.9, "payload": {"document_id": "doc-2", "text": "conflict text", "title": "Doc2.md"}}
    ]
    with patch.object(service, "_get_document_chunks") as mock_get:
        mock_get.return_value = [
            {"id": "chunk-1", "text": "some text", "document_id": "doc-1", "title": "Doc1.md", "project_id": "proj-1"}
        ]
        await service.scan_document("doc-1", "proj-1")

    mock_repo.create.assert_called_once()
    call_kwargs = mock_repo.create.call_args.kwargs
    assert call_kwargs["chunk_a_id"] == "chunk-1"
    assert call_kwargs["chunk_b_id"] == "other-chunk"
    assert call_kwargs["document_a_title"] == "Doc1.md"
    assert call_kwargs["document_b_title"] == "Doc2.md"
    assert call_kwargs["explanation"] == "They conflict"
