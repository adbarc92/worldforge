from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.models.database import engine
from app.dependencies import get_llm_service, get_qdrant_service
from app.api.v1 import router as api_router
from app.api.v1.openai_compat import router as openai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Canon Builder API")

    qdrant = get_qdrant_service()
    await qdrant.ensure_collection()
    logger.info("Qdrant collection verified")

    llm = get_llm_service()
    status = await llm.check_available()
    for provider, available in status.items():
        level = "info" if available else "warning"
        getattr(logger, level)(f"LLM {provider}: {'available' if available else 'UNAVAILABLE'}")

    logger.info("Canon Builder API ready")
    yield

    # Shutdown
    qdrant = get_qdrant_service()
    await qdrant.close()
    await engine.dispose()
    logger.info("Canon Builder API shut down")


app = FastAPI(
    title="Canon Builder",
    description="RAG-powered worldbuilding knowledge system",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(openai_router)


@app.get("/health")
async def health():
    llm = get_llm_service()
    status = await llm.check_available()
    return {
        "status": "healthy" if all(status.values()) else "degraded",
        "services": status,
    }
