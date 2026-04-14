import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def settings_snapshot():
    """Snapshot/restore global settings to prevent test pollution."""
    from app.core.config import settings
    snapshot = {
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "ANTHROPIC_MODEL": settings.ANTHROPIC_MODEL,
        "OPENAI_EMBEDDING_MODEL": settings.OPENAI_EMBEDDING_MODEL,
    }
    yield settings
    for k, v in snapshot.items():
        setattr(settings, k, v)


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


@pytest.mark.asyncio
async def test_put_settings_updates_and_returns_health(settings_snapshot):
    """PUT /settings updates config and returns settings + health."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    mock_health = {"anthropic": True, "openai": True}

    with (
        patch("app.api.v1.settings.reset_llm_service") as mock_reset,
        patch("app.api.v1.settings.get_llm_service") as mock_get_llm,
    ):
        mock_llm = MagicMock()

        async def _check():
            return mock_health

        mock_llm.check_available = _check
        mock_get_llm.return_value = mock_llm

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.put(
                "/api/v1/settings",
                json={"anthropic_model": "claude-sonnet-4-20250514"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert "settings" in data
    assert "health" in data
    assert data["health"]["status"] == "healthy"
    mock_reset.assert_called_once()


@pytest.mark.asyncio
async def test_put_settings_ignores_masked_key(settings_snapshot):
    """PUT /settings ignores API keys that contain masked characters."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    app_settings = settings_snapshot
    original_key = app_settings.ANTHROPIC_API_KEY

    mock_health = {"anthropic": True, "openai": True}

    with (
        patch("app.api.v1.settings.reset_llm_service"),
        patch("app.api.v1.settings.get_llm_service") as mock_get_llm,
    ):
        async def _check():
            return mock_health

        mock_llm = MagicMock()
        mock_llm.check_available = _check
        mock_get_llm.return_value = mock_llm

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.put(
                "/api/v1/settings",
                json={"anthropic_api_key": "sk-ant-***hijk"},
            )

    assert resp.status_code == 200
    # The key should not have been changed to the masked value
    assert app_settings.ANTHROPIC_API_KEY == original_key
