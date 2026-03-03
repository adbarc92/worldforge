import pytest


def test_mask_api_key():
    from app.api.v1.settings import mask_key

    assert mask_key("sk-ant-api03-abcdefghijk") == "sk-an***hijk"
    assert mask_key("sk-proj-abcdefghijklmnop") == "sk-pr***mnop"
    assert mask_key("short") == "****"
    assert mask_key("") == ""


@pytest.mark.asyncio
async def test_get_settings():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "anthropic_api_key" in data
        assert "anthropic_model" in data
        # Keys should be masked
        if data["anthropic_api_key"]:
            assert "***" in data["anthropic_api_key"]
