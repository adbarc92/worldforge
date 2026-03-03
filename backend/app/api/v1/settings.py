from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.dependencies import get_llm_service, reset_llm_service

router = APIRouter(prefix="/settings", tags=["settings"])


def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:5]}***{key[-4:]}"


class SettingsResponse(BaseModel):
    anthropic_api_key: str
    openai_api_key: str
    anthropic_model: str
    openai_embedding_model: str


class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_model: str | None = None
    openai_embedding_model: str | None = None


@router.get("", response_model=SettingsResponse)
async def get_settings():
    return SettingsResponse(
        anthropic_api_key=mask_key(settings.ANTHROPIC_API_KEY),
        openai_api_key=mask_key(settings.OPENAI_API_KEY),
        anthropic_model=settings.ANTHROPIC_MODEL,
        openai_embedding_model=settings.OPENAI_EMBEDDING_MODEL,
    )


@router.put("")
async def update_settings(data: SettingsUpdate):
    if data.anthropic_api_key and "***" not in data.anthropic_api_key:
        settings.ANTHROPIC_API_KEY = data.anthropic_api_key
    if data.openai_api_key and "***" not in data.openai_api_key:
        settings.OPENAI_API_KEY = data.openai_api_key
    if data.anthropic_model:
        settings.ANTHROPIC_MODEL = data.anthropic_model
    if data.openai_embedding_model:
        settings.OPENAI_EMBEDDING_MODEL = data.openai_embedding_model

    # Reset LLM service so it picks up new settings
    reset_llm_service()

    # Check new health
    llm = get_llm_service()
    health = await llm.check_available()

    return {
        "settings": SettingsResponse(
            anthropic_api_key=mask_key(settings.ANTHROPIC_API_KEY),
            openai_api_key=mask_key(settings.OPENAI_API_KEY),
            anthropic_model=settings.ANTHROPIC_MODEL,
            openai_embedding_model=settings.OPENAI_EMBEDDING_MODEL,
        ),
        "health": {
            "status": "healthy" if all(health.values()) else "degraded",
            "services": health,
        },
    }
