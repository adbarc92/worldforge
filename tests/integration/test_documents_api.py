"""
Integration tests for documents API.
Tests: TEST-INT-001 through TEST-INT-007
"""

import pytest
from httpx import AsyncClient
from pathlib import Path


@pytest.fixture
async def app():
    """Get FastAPI app instance."""
    from backend.app.main import app
    return app


@pytest.fixture
async def client(app):
    """Get async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestDocumentsAPI:
    """Integration tests for document upload and management APIs."""

    # TEST-INT-005: List All Documents
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_all_documents(self, client):
        """Test listing all documents."""
        response = await client.get("/api/documents/")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)
        assert isinstance(data["total"], int)

    # TEST-INT-006: List with Pagination
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_with_pagination(self, client):
        """Test document listing pagination."""
        response = await client.get("/api/documents/?skip=0&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) <= 5

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_with_status_filter(self, client):
        """Test listing documents with status filter."""
        response = await client.get("/api/documents/?status_filter=active")

        assert response.status_code == 200
        data = response.json()
        # All returned documents should be active
        assert all(doc["status"] == "active" for doc in data["documents"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root API endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


# Note: Full upload tests require sample files
# These are marked as skipped unless fixtures are available

class TestDocumentUpload:
    """Tests for document upload workflow."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.skipif(
        not Path("tests/fixtures/documents/sample.md").exists(),
        reason="Sample markdown file not found"
    )
    @pytest.mark.asyncio
    async def test_upload_markdown_document(self, client):
        """TEST-INT-001: Test uploading markdown document."""
        with open("tests/fixtures/documents/sample.md", "rb") as f:
            files = {"file": ("test.md", f, "text/markdown")}
            params = {"title": "Test Markdown", "extract_entities": False}

            response = await client.post(
                "/api/documents/upload",
                files=files,
                params=params
            )

        assert response.status_code == 200
        data = response.json()

        assert "document" in data
        assert data["document"]["title"] == "Test Markdown"
        assert data["chunks_created"] > 0

    # TEST-INT-003: Reject Unsupported File Type
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reject_unsupported_file_type(self, client):
        """Test API rejects unsupported file formats."""
        files = {"file": ("test.xlsx", b"fake excel data", "application/vnd.ms-excel")}

        response = await client.post("/api/documents/upload", files=files)

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_upload_without_file(self, client):
        """Test upload endpoint requires file."""
        response = await client.post("/api/documents/upload")

        # Should return 422 (validation error)
        assert response.status_code == 422


class TestDocumentRetrieval:
    """Tests for document retrieval."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("tests/fixtures/documents/sample.md").exists(),
        reason="Sample file not found"
    )
    @pytest.mark.asyncio
    async def test_get_document_by_id(self, client):
        """Test retrieving document by ID."""
        # First upload a document
        with open("tests/fixtures/documents/sample.md", "rb") as f:
            files = {"file": ("test.md", f, "text/markdown")}
            upload_response = await client.post(
                "/api/documents/upload",
                files=files,
                params={"extract_entities": False}
            )

        document_id = upload_response.json()["document"]["id"]

        # Now retrieve it
        response = await client.get(f"/api/documents/{document_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, client):
        """Test retrieving non-existent document returns 404."""
        response = await client.get("/api/documents/nonexistent-id")

        assert response.status_code == 404


class TestDocumentDeletion:
    """Tests for document deletion."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("tests/fixtures/documents/sample.md").exists(),
        reason="Sample file not found"
    )
    @pytest.mark.asyncio
    async def test_delete_document(self, client):
        """Test deleting a document."""
        # First upload a document
        with open("tests/fixtures/documents/sample.md", "rb") as f:
            files = {"file": ("test.md", f, "text/markdown")}
            upload_response = await client.post(
                "/api/documents/upload",
                files=files,
                params={"extract_entities": False}
            )

        document_id = upload_response.json()["document"]["id"]

        # Delete it
        response = await client.delete(f"/api/documents/{document_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's gone
        get_response = await client.get(f"/api/documents/{document_id}")
        assert get_response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, client):
        """Test deleting non-existent document returns 404."""
        response = await client.delete("/api/documents/nonexistent-id")

        assert response.status_code == 404
