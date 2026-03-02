import os
import pytest
import tempfile
from httpx import AsyncClient, ASGITransport
from app.main import app


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_upload_and_query_pipeline():
    """Upload a document, then query it and verify we get a relevant answer."""
    transport = ASGITransport(app=app)

    content = """
    The Kingdom of Eldoria is a vast realm in the northern continent.
    Its capital city is Thornwall, built upon ancient dwarven ruins.
    The current ruler is Queen Seraphina, who took the throne after
    the War of Silver Flames in the year 1247.
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Upload
            with open(temp_path, "rb") as f:
                response = await client.post(
                    "/api/v1/documents/upload",
                    files={"file": ("eldoria.txt", f, "text/plain")},
                )
            assert response.status_code == 200
            doc = response.json()
            assert doc["status"] == "completed"
            assert doc["chunk_count"] > 0

            # Query
            response = await client.post(
                "/api/v1/query",
                json={"question": "What is the capital of Eldoria?"},
            )
            assert response.status_code == 200
            result = response.json()
            assert "Thornwall" in result["answer"]
            assert len(result["citations"]) > 0

            # Delete
            response = await client.delete(f"/api/v1/documents/{doc['id']}")
            assert response.status_code == 200

            # Verify deleted
            response = await client.get(f"/api/v1/documents/{doc['id']}")
            assert response.status_code == 404
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
