import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ingestion_service import IngestionService


@pytest.fixture
def mock_services():
    mock_llm = AsyncMock()
    mock_llm.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    mock_qdrant = AsyncMock()
    mock_repo = AsyncMock()
    mock_doc = MagicMock()
    mock_doc.id = "doc1"
    mock_repo.create = AsyncMock(return_value=mock_doc)
    mock_repo.update_status = AsyncMock(return_value=mock_doc)
    return mock_llm, mock_qdrant, mock_repo, mock_doc


@pytest.mark.asyncio
async def test_extract_text_from_txt():
    service = IngestionService(
        llm_service=AsyncMock(),
        qdrant_service=AsyncMock(),
        document_repo=AsyncMock(),
    )
    content = "Hello, this is test content.\nLine two."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name
    try:
        result = await service._extract_text(tmp_path)
        assert result == content
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_chunk_text():
    service = IngestionService(
        llm_service=AsyncMock(),
        qdrant_service=AsyncMock(),
        document_repo=AsyncMock(),
    )
    service.chunk_size = 512
    service.chunk_overlap = 50

    long_text = "This is a sentence for chunking. " * 200  # ~6600 chars, well over 512 tokens
    chunks = service._chunk_text(long_text, document_id="doc1", title="Test Doc", project_id="proj-1")

    assert len(chunks) > 1
    expected_keys = {"text", "chunk_id", "document_id", "title", "chunk_index", "project_id"}
    for chunk in chunks:
        assert set(chunk.keys()) == expected_keys
        assert chunk["document_id"] == "doc1"
        assert chunk["title"] == "Test Doc"
        assert chunk["project_id"] == "proj-1"
        # chunk_id is a UUID
        assert len(chunk["chunk_id"]) == 36


@pytest.mark.asyncio
async def test_process_document_pipeline(mock_services):
    mock_llm, mock_qdrant, mock_repo, mock_doc = mock_services

    service = IngestionService(
        llm_service=mock_llm,
        qdrant_service=mock_qdrant,
        document_repo=mock_repo,
    )
    service.chunk_size = 5000
    service.chunk_overlap = 50

    content = "Test document content for the pipeline."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name

    try:
        result = await service.process_document(tmp_path, title="Pipeline Test", project_id="proj-1")

        mock_repo.create.assert_called_once_with(title="Pipeline Test", file_path=tmp_path, project_id="proj-1")
        mock_llm.embed.assert_called_once()
        embed_arg = mock_llm.embed.call_args[0][0]
        assert isinstance(embed_arg, list)
        assert content in embed_arg[0]

        mock_qdrant.upsert.assert_called_once()

        status_calls = [call.args for call in mock_repo.update_status.call_args_list]
        assert ("doc1", "processing") in status_calls
        completed_calls = [
            c for c in mock_repo.update_status.call_args_list
            if c.args == ("doc1", "completed")
        ]
        assert len(completed_calls) == 1

        assert result == mock_doc
    finally:
        os.unlink(tmp_path)
