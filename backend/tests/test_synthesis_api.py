import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import get_db
from app.models.project_repository import ProjectRepository


PROJECT_ID = "proj-001"
SYNTHESIS_ID = "synth-001"
BASE_URL = f"/api/v1/projects/{PROJECT_ID}/synthesis"


def _make_synthesis(**overrides):
    """Create a mock synthesis object with default values."""
    s = MagicMock()
    defaults = {
        "id": SYNTHESIS_ID,
        "project_id": PROJECT_ID,
        "title": "World Primer",
        "outline": [{"title": "Cosmogony", "description": "How the world began"}],
        "outline_approved": False,
        "content": None,
        "status": "outline_pending",
        "error_message": None,
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
        "updated_at": datetime(2026, 1, 1, 12, 0, 0),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


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
async def test_create_synthesis_blocked_by_contradictions(mock_db, mock_project):
    """POST /synthesis returns 400 when open contradictions exist."""
    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.ContradictionRepository") as MockContraRepo,
    ):
        contra_instance = MockContraRepo.return_value
        contra_instance.count = AsyncMock(return_value=5)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(BASE_URL)
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 400
    assert "contradictions" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_synthesis_succeeds(mock_db, mock_project):
    """POST /synthesis returns 202 when no contradictions and creates background task."""
    synthesis = _make_synthesis()

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.ContradictionRepository") as MockContraRepo,
        patch("app.api.v1.synthesis.SynthesisRepository") as MockSynthRepo,
        patch("app.api.v1.synthesis.asyncio") as mock_asyncio,
    ):
        contra_instance = MockContraRepo.return_value
        contra_instance.count = AsyncMock(return_value=0)

        synth_instance = MockSynthRepo.return_value
        synth_instance.create = AsyncMock(return_value=synthesis)

        mock_asyncio.create_task = MagicMock()

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(BASE_URL)
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 202
    data = resp.json()
    assert data["id"] == SYNTHESIS_ID
    assert data["project_id"] == PROJECT_ID
    mock_asyncio.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_get_synthesis(mock_db, mock_project):
    """GET /synthesis/{id} returns the synthesis."""
    synthesis = _make_synthesis(status="outline_ready")

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.SynthesisRepository") as MockSynthRepo,
    ):
        synth_instance = MockSynthRepo.return_value
        synth_instance.get = AsyncMock(return_value=synthesis)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"{BASE_URL}/{SYNTHESIS_ID}")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "outline_ready"
    assert data["id"] == SYNTHESIS_ID


@pytest.mark.asyncio
async def test_update_outline(mock_db, mock_project):
    """PATCH /synthesis/{id}/outline updates the outline."""
    synthesis = _make_synthesis(status="outline_ready", outline_approved=False)
    updated = _make_synthesis(
        status="outline_ready",
        outline_approved=False,
        outline=[{"title": "New Section", "description": "New desc"}],
    )

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.SynthesisRepository") as MockSynthRepo,
    ):
        synth_instance = MockSynthRepo.return_value
        synth_instance.get = AsyncMock(return_value=synthesis)
        synth_instance.update_outline = AsyncMock(return_value=updated)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(
                    f"{BASE_URL}/{SYNTHESIS_ID}/outline",
                    json={"outline": [{"title": "New Section", "description": "New desc"}]},
                )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["outline"][0]["title"] == "New Section"


@pytest.mark.asyncio
async def test_update_outline_rejected_after_approval(mock_db, mock_project):
    """PATCH /synthesis/{id}/outline returns 409 when outline already approved."""
    synthesis = _make_synthesis(status="outline_ready", outline_approved=True)

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.SynthesisRepository") as MockSynthRepo,
    ):
        synth_instance = MockSynthRepo.return_value
        synth_instance.get = AsyncMock(return_value=synthesis)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.patch(
                    f"{BASE_URL}/{SYNTHESIS_ID}/outline",
                    json={"outline": [{"title": "X", "description": "Y"}]},
                )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_approve_rejected_wrong_status(mock_db, mock_project):
    """POST /synthesis/{id}/approve returns 409 when status is not outline_ready."""
    synthesis = _make_synthesis(status="generating")

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.SynthesisRepository") as MockSynthRepo,
    ):
        synth_instance = MockSynthRepo.return_value
        synth_instance.get = AsyncMock(return_value=synthesis)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"{BASE_URL}/{SYNTHESIS_ID}/approve")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_download_completed(mock_db, mock_project):
    """GET /synthesis/{id}/download returns markdown file when completed."""
    synthesis = _make_synthesis(
        status="completed",
        content="# Cosmogony\n\nIn the beginning...",
        title="World Primer",
    )

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.SynthesisRepository") as MockSynthRepo,
    ):
        synth_instance = MockSynthRepo.return_value
        synth_instance.get = AsyncMock(return_value=synthesis)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"{BASE_URL}/{SYNTHESIS_ID}/download")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert "World_Primer.md" in resp.headers.get("content-disposition", "")
    assert resp.text == "# Cosmogony\n\nIn the beginning..."


@pytest.mark.asyncio
async def test_download_rejected_incomplete(mock_db, mock_project):
    """GET /synthesis/{id}/download returns 409 when synthesis not completed."""
    synthesis = _make_synthesis(status="outline_ready")

    with (
        patch.object(ProjectRepository, "get", return_value=mock_project),
        patch("app.api.v1.synthesis.SynthesisRepository") as MockSynthRepo,
    ):
        synth_instance = MockSynthRepo.return_value
        synth_instance.get = AsyncMock(return_value=synthesis)

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"{BASE_URL}/{SYNTHESIS_ID}/download")
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 409
