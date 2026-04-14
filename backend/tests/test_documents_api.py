import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import get_db
from app.dependencies import get_ingestion_service, get_contradiction_service


PROJECT_ID = "proj-001"
DOC_ID = "doc-001"
BASE_URL = f"/api/v1/projects/{PROJECT_ID}/documents"


def _make_document(**overrides):
    """Create a mock document object with default values."""
    d = MagicMock()
    defaults = {
        "id": DOC_ID,
        "title": "test.md",
        "status": "ready",
        "chunk_count": 5,
        "project_id": PROJECT_ID,
        "file_path": "/uploads/test.md",
        "error_message": None,
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(d, k, v)
    return d


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_project():
    project = MagicMock()
    project.id = PROJECT_ID
    project.name = "Test Project"
    return project


# --- POST /api/v1/projects/{pid}/documents/upload ---


@pytest.mark.asyncio
async def test_upload_document(mock_db, mock_project):
    """POST /documents/upload ingests a file and returns the document."""
    doc = _make_document()

    mock_ingestion = AsyncMock()
    mock_ingestion.process_document = AsyncMock(return_value=doc)

    mock_contradiction_svc = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion
    app.dependency_overrides[get_contradiction_service] = lambda: mock_contradiction_svc
    try:
        with (
            patch("app.api.v1.documents.ProjectRepository") as MockProjRepo,
            patch("app.api.v1.documents.asyncio") as mock_asyncio,
            patch("app.api.v1.documents.aiofiles", new=MagicMock()),
            patch("app.api.v1.documents.os") as mock_os,
        ):
            proj_repo = MockProjRepo.return_value
            proj_repo.get = AsyncMock(return_value=mock_project)

            mock_asyncio.create_task = MagicMock()
            mock_os.path.splitext = lambda f: ("test", ".md")
            mock_os.makedirs = MagicMock()
            mock_os.path.join = lambda *args: "/uploads/fake.md"

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    f"{BASE_URL}/upload",
                    files={"file": ("test.md", b"# Hello World", "text/markdown")},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == DOC_ID
    assert data["title"] == "test.md"
    assert data["status"] == "ready"
    assert data["project_id"] == PROJECT_ID


@pytest.mark.asyncio
async def test_upload_unsupported_file_type(mock_db, mock_project):
    """POST /documents/upload rejects unsupported file types."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ingestion_service] = lambda: AsyncMock()
    app.dependency_overrides[get_contradiction_service] = lambda: AsyncMock()
    try:
        with patch("app.api.v1.documents.ProjectRepository") as MockProjRepo:
            proj_repo = MockProjRepo.return_value
            proj_repo.get = AsyncMock(return_value=mock_project)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    f"{BASE_URL}/upload",
                    files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_project_not_found(mock_db):
    """POST /documents/upload returns 404 when project doesn't exist."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ingestion_service] = lambda: AsyncMock()
    app.dependency_overrides[get_contradiction_service] = lambda: AsyncMock()
    try:
        with patch("app.api.v1.documents.ProjectRepository") as MockProjRepo:
            proj_repo = MockProjRepo.return_value
            proj_repo.get = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    f"{BASE_URL}/upload",
                    files={"file": ("test.md", b"# Hello", "text/markdown")},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


# --- GET /api/v1/projects/{pid}/documents ---


@pytest.mark.asyncio
async def test_list_documents(mock_db, mock_project):
    """GET /documents returns a list of documents."""
    doc = _make_document()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with (
            patch("app.api.v1.documents.ProjectRepository") as MockProjRepo,
            patch("app.api.v1.documents.DocumentRepository") as MockDocRepo,
        ):
            proj_repo = MockProjRepo.return_value
            proj_repo.get = AsyncMock(return_value=mock_project)

            doc_repo = MockDocRepo.return_value
            doc_repo.list = AsyncMock(return_value=[doc])

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(BASE_URL)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == DOC_ID
    assert data[0]["title"] == "test.md"


# --- GET /api/v1/projects/{pid}/documents/{id} ---


@pytest.mark.asyncio
async def test_get_document(mock_db, mock_project):
    """GET /documents/{id} returns the document."""
    doc = _make_document()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with (
            patch("app.api.v1.documents.ProjectRepository") as MockProjRepo,
            patch("app.api.v1.documents.DocumentRepository") as MockDocRepo,
        ):
            proj_repo = MockProjRepo.return_value
            proj_repo.get = AsyncMock(return_value=mock_project)

            doc_repo = MockDocRepo.return_value
            doc_repo.get = AsyncMock(return_value=doc)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"{BASE_URL}/{DOC_ID}")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == DOC_ID
    assert data["title"] == "test.md"
    assert data["file_path"] == "/uploads/test.md"


@pytest.mark.asyncio
async def test_get_document_not_found(mock_db, mock_project):
    """GET /documents/{id} returns 404 when document doesn't exist."""
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with (
            patch("app.api.v1.documents.ProjectRepository") as MockProjRepo,
            patch("app.api.v1.documents.DocumentRepository") as MockDocRepo,
        ):
            proj_repo = MockProjRepo.return_value
            proj_repo.get = AsyncMock(return_value=mock_project)

            doc_repo = MockDocRepo.return_value
            doc_repo.get = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"{BASE_URL}/nonexistent-id")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Document not found"


# --- DELETE /api/v1/projects/{pid}/documents/{id} ---


@pytest.mark.asyncio
async def test_delete_document(mock_db, mock_project):
    """DELETE /documents/{id} deletes the document."""
    doc = _make_document()

    mock_ingestion = AsyncMock()
    mock_ingestion.delete_document = AsyncMock(return_value=True)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion
    try:
        with (
            patch("app.api.v1.documents.ProjectRepository") as MockProjRepo,
            patch("app.api.v1.documents.DocumentRepository") as MockDocRepo,
        ):
            proj_repo = MockProjRepo.return_value
            proj_repo.get = AsyncMock(return_value=mock_project)

            doc_repo = MockDocRepo.return_value
            doc_repo.get = AsyncMock(return_value=doc)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.delete(f"{BASE_URL}/{DOC_ID}")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    mock_ingestion.delete_document.assert_awaited_once_with(DOC_ID)
