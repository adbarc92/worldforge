import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import get_db
from app.models.project_repository import ProjectRepository


PROJECT_ID = "proj-001"
CONTRADICTION_ID = "contra-001"
BASE_URL = f"/api/v1/projects/{PROJECT_ID}/contradictions"


def _make_contradiction(**overrides):
    """Create a mock contradiction object with default values."""
    c = MagicMock()
    defaults = {
        "id": CONTRADICTION_ID,
        "chunk_a_text": "The sky is blue.",
        "chunk_b_text": "The sky is green.",
        "document_a_id": "doc-a",
        "document_b_id": "doc-b",
        "document_a_title": "Doc A",
        "document_b_title": "Doc B",
        "explanation": "Conflicting sky colour.",
        "status": "open",
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
        "resolved_at": None,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(c, k, v)
    return c


@pytest.fixture
def mock_db():
    session = AsyncMock()
    return session


@pytest.fixture
def mock_project():
    project = MagicMock()
    project.id = PROJECT_ID
    project.name = "Test Project"
    return project


@pytest.mark.asyncio
async def test_list_contradictions(mock_db, mock_project):
    """GET /contradictions returns items and total."""
    contradiction = _make_contradiction()

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo,
    ):
        repo_instance = MockRepo.return_value
        repo_instance.list = AsyncMock(return_value=[contradiction])
        repo_instance.count = AsyncMock(return_value=1)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(BASE_URL)
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["id"] == CONTRADICTION_ID
    assert item["explanation"] == "Conflicting sky colour."
    assert item["status"] == "open"


@pytest.mark.asyncio
async def test_scan_returns_202(mock_db, mock_project):
    """POST /contradictions/scan returns 202 with scan_started status."""
    with patch.object(ProjectRepository, "get", return_value=mock_project):
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"{BASE_URL}/scan")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "scan_started"
    assert data["project_id"] == PROJECT_ID


@pytest.mark.asyncio
async def test_resolve_contradiction(mock_db, mock_project):
    """PATCH /contradictions/{id}/resolve returns updated status."""
    resolved = _make_contradiction(status="resolved", resolved_at=datetime(2026, 1, 2))

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo,
    ):
        repo_instance = MockRepo.return_value
        repo_instance.update_status = AsyncMock(return_value=resolved)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(f"{BASE_URL}/{CONTRADICTION_ID}/resolve")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == CONTRADICTION_ID
    assert data["status"] == "resolved"


@pytest.mark.asyncio
async def test_dismiss_contradiction(mock_db, mock_project):
    """PATCH /contradictions/{id}/dismiss returns updated status."""
    dismissed = _make_contradiction(status="dismissed", resolved_at=datetime(2026, 1, 2))

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo,
    ):
        repo_instance = MockRepo.return_value
        repo_instance.update_status = AsyncMock(return_value=dismissed)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(f"{BASE_URL}/{CONTRADICTION_ID}/dismiss")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == CONTRADICTION_ID
    assert data["status"] == "dismissed"


@pytest.mark.asyncio
async def test_resolve_nonexistent_returns_404(mock_db, mock_project):
    """PATCH /contradictions/{id}/resolve returns 404 when not found."""
    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo,
    ):
        repo_instance = MockRepo.return_value
        repo_instance.update_status = AsyncMock(return_value=None)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(f"{BASE_URL}/nonexistent-id/resolve")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Contradiction not found"


@pytest.mark.asyncio
async def test_reopen_contradiction(mock_db, mock_project):
    """PATCH /contradictions/{id}/reopen returns updated status."""
    reopened = _make_contradiction(status="open", resolved_at=None)

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo,
    ):
        repo_instance = MockRepo.return_value
        repo_instance.update_status = AsyncMock(return_value=reopened)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(f"{BASE_URL}/{CONTRADICTION_ID}/reopen")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == CONTRADICTION_ID
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_reopen_nonexistent_returns_404(mock_db, mock_project):
    """PATCH /contradictions/{id}/reopen returns 404 when not found."""
    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo,
    ):
        repo_instance = MockRepo.return_value
        repo_instance.update_status = AsyncMock(return_value=None)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(f"{BASE_URL}/nonexistent-id/reopen")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Contradiction not found"


@pytest.mark.asyncio
async def test_bulk_update_contradictions(mock_db, mock_project):
    """POST /contradictions/bulk resolves multiple contradictions."""
    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.contradictions.ContradictionRepository") as MockRepo,
    ):
        repo_instance = MockRepo.return_value
        repo_instance.bulk_update_status = AsyncMock(return_value=2)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    f"{BASE_URL}/bulk",
                    json={"ids": ["c1", "c2"], "status": "resolved", "note": "batch fix"},
                )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["updated"] == 2
    assert data["status"] == "resolved"


@pytest.mark.asyncio
async def test_bulk_update_invalid_status(mock_db, mock_project):
    """POST /contradictions/bulk rejects invalid status values."""
    with patch.object(ProjectRepository, "get", return_value=mock_project):
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    f"{BASE_URL}/bulk",
                    json={"ids": ["c1"], "status": "invalid_status"},
                )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 400
    assert "resolved" in resp.json()["detail"] or "dismissed" in resp.json()["detail"]
