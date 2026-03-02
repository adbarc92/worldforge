"""Tests for DocumentRepository."""

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest

from app.models.database import Document
from app.models.repositories import DocumentRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session


@pytest.fixture
def repo(mock_session):
    return DocumentRepository(mock_session)


@pytest.mark.asyncio
async def test_document_repository_create(repo, mock_session):
    """Verify Document is created with correct fields, session.add and commit called."""
    doc = await repo.create(title="Test Document", file_path="/uploads/test.pdf")

    # Verify session.add was called with a Document instance
    mock_session.add.assert_called_once()
    added_doc = mock_session.add.call_args[0][0]
    assert isinstance(added_doc, Document)
    assert added_doc.title == "Test Document"
    assert added_doc.file_path == "/uploads/test.pdf"
    assert added_doc.status == "pending"
    assert added_doc.id is not None  # UUID was assigned

    # Verify commit and refresh were called
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(added_doc)


@pytest.mark.asyncio
async def test_document_repository_list(repo, mock_session):
    """Mock execute result, verify list returns docs."""
    # Create mock documents
    doc1 = Document(id="id-1", title="Doc 1", file_path="/a.pdf", status="pending")
    doc2 = Document(id="id-2", title="Doc 2", file_path="/b.pdf", status="processed")

    # Set up the mock chain: session.execute() -> result.scalars().all()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [doc1, doc2]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    docs = await repo.list(skip=0, limit=50)

    assert len(docs) == 2
    assert docs[0].title == "Doc 1"
    assert docs[1].title == "Doc 2"
    mock_session.execute.assert_awaited_once()
