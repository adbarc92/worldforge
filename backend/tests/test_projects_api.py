import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import get_db


PROJECT_ID = "proj-001"
BASE_URL = "/api/v1/projects"


def _make_project(**overrides):
    """Create a mock project object with default values."""
    p = MagicMock()
    defaults = {
        "id": PROJECT_ID,
        "name": "Test Project",
        "description": "A test project",
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
        "updated_at": datetime(2026, 1, 1, 12, 0, 0),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


@pytest.fixture
def mock_db():
    return AsyncMock()


# --- POST /api/v1/projects ---


@pytest.mark.asyncio
async def test_create_project(mock_db):
    """POST /projects creates a project and returns it."""
    project = _make_project()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("app.api.v1.projects.ProjectRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.create = AsyncMock(return_value=project)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    BASE_URL,
                    json={"name": "Test Project", "description": "A test project"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == PROJECT_ID
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project"


@pytest.mark.asyncio
async def test_create_project_empty_name_fails(mock_db):
    """POST /projects with empty body returns 422."""
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(BASE_URL, json={})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422


# --- GET /api/v1/projects ---


@pytest.mark.asyncio
async def test_list_projects(mock_db):
    """GET /projects returns a list of projects."""
    project = _make_project()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("app.api.v1.projects.ProjectRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.list = AsyncMock(return_value=[project])
            repo.get_document_count = AsyncMock(return_value=3)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(BASE_URL)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == PROJECT_ID
    assert data[0]["document_count"] == 3


# --- GET /api/v1/projects/{id} ---


@pytest.mark.asyncio
async def test_get_project(mock_db):
    """GET /projects/{id} returns the project."""
    project = _make_project()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("app.api.v1.projects.ProjectRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get = AsyncMock(return_value=project)
            repo.get_document_count = AsyncMock(return_value=5)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"{BASE_URL}/{PROJECT_ID}")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == PROJECT_ID
    assert data["name"] == "Test Project"
    assert data["document_count"] == 5


@pytest.mark.asyncio
async def test_get_project_not_found(mock_db):
    """GET /projects/{id} returns 404 when project doesn't exist."""
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("app.api.v1.projects.ProjectRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"{BASE_URL}/nonexistent-id")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


# --- PUT /api/v1/projects/{id} ---


@pytest.mark.asyncio
async def test_update_project(mock_db):
    """PUT /projects/{id} updates and returns the project."""
    updated = _make_project(name="Updated Name", description="Updated desc")

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("app.api.v1.projects.ProjectRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.update = AsyncMock(return_value=updated)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.put(
                    f"{BASE_URL}/{PROJECT_ID}",
                    json={"name": "Updated Name", "description": "Updated desc"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated desc"


@pytest.mark.asyncio
async def test_update_project_not_found(mock_db):
    """PUT /projects/{id} returns 404 when project doesn't exist."""
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("app.api.v1.projects.ProjectRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.update = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.put(
                    f"{BASE_URL}/nonexistent-id",
                    json={"name": "Nope"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


# --- DELETE /api/v1/projects/{id} ---


@pytest.mark.asyncio
async def test_delete_project(mock_db):
    """DELETE /projects/{id} deletes the project and its vectors."""
    project = _make_project()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with (
            patch("app.api.v1.projects.ProjectRepository") as MockRepo,
            patch("app.api.v1.projects.get_qdrant_service") as mock_qdrant_fn,
        ):
            repo = MockRepo.return_value
            repo.get = AsyncMock(return_value=project)
            repo.delete = AsyncMock(return_value=True)

            mock_qdrant = AsyncMock()
            mock_qdrant.delete_by_project = AsyncMock()
            mock_qdrant_fn.return_value = mock_qdrant

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.delete(f"{BASE_URL}/{PROJECT_ID}")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    mock_qdrant.delete_by_project.assert_awaited_once_with(PROJECT_ID)


@pytest.mark.asyncio
async def test_delete_project_not_found(mock_db):
    """DELETE /projects/{id} returns 404 when project doesn't exist."""
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with (
            patch("app.api.v1.projects.ProjectRepository") as MockRepo,
            patch("app.api.v1.projects.get_qdrant_service") as mock_qdrant_fn,
        ):
            repo = MockRepo.return_value
            repo.get = AsyncMock(return_value=None)

            mock_qdrant = AsyncMock()
            mock_qdrant_fn.return_value = mock_qdrant

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.delete(f"{BASE_URL}/nonexistent-id")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"
