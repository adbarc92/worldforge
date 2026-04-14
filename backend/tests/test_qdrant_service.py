"""Tests for QdrantService (async)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.qdrant_service import QdrantService


@pytest.fixture
def service():
    """Create QdrantService bypassing __init__ to avoid real connection."""
    svc = QdrantService.__new__(QdrantService)
    svc.client = AsyncMock()
    svc.collection_name = "canon_documents"
    return svc


@pytest.mark.asyncio
async def test_qdrant_upsert(service):
    ids = ["id-1", "id-2"]
    vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    payloads = [{"doc": "a"}, {"doc": "b"}]

    await service.upsert(ids, vectors, payloads)

    service.client.upsert.assert_awaited_once()
    call_kwargs = service.client.upsert.call_args
    assert call_kwargs.kwargs["collection_name"] == "canon_documents"
    points = call_kwargs.kwargs["points"]
    assert len(points) == 2
    assert points[0].id == "id-1"
    assert points[0].vector == [0.1, 0.2, 0.3]
    assert points[0].payload == {"doc": "a"}


@pytest.mark.asyncio
async def test_qdrant_search(service):
    mock_point = MagicMock()
    mock_point.id = "pt-1"
    mock_point.score = 0.95
    mock_point.payload = {"title": "Test"}

    mock_response = MagicMock()
    mock_response.points = [mock_point]
    service.client.query_points = AsyncMock(return_value=mock_response)

    results = await service.search(query_vector=[0.1, 0.2, 0.3], top_k=5)

    service.client.query_points.assert_awaited_once()
    assert len(results) == 1
    assert results[0]["id"] == "pt-1"
    assert results[0]["score"] == 0.95
    assert results[0]["payload"] == {"title": "Test"}


@pytest.mark.asyncio
async def test_qdrant_search_with_filters(service):
    mock_response = MagicMock()
    mock_response.points = []
    service.client.query_points = AsyncMock(return_value=mock_response)

    await service.search(
        query_vector=[0.1, 0.2],
        filters={"document_id": "doc-123"},
    )

    call_kwargs = service.client.query_points.call_args.kwargs
    assert call_kwargs["query_filter"] is not None


@pytest.mark.asyncio
async def test_qdrant_delete_by_document(service):
    await service.delete_by_document("doc-42")

    service.client.delete.assert_awaited_once()
    call_kwargs = service.client.delete.call_args.kwargs
    assert call_kwargs["collection_name"] == "canon_documents"
    # Verify the filter contains document_id match
    points_selector = call_kwargs["points_selector"]
    assert points_selector.must[0].key == "document_id"
    assert points_selector.must[0].match.value == "doc-42"


@pytest.mark.asyncio
async def test_qdrant_delete_by_project(service):
    await service.delete_by_project("proj-42")

    service.client.delete.assert_awaited_once()
    call_kwargs = service.client.delete.call_args.kwargs
    assert call_kwargs["collection_name"] == "canon_documents"
    points_selector = call_kwargs["points_selector"]
    assert points_selector.must[0].key == "project_id"
    assert points_selector.must[0].match.value == "proj-42"
