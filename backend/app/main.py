from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from app.core.config import settings
from app.models.database import engine
from app.dependencies import get_llm_service, get_qdrant_service
from app.api.v1 import router as api_router
from app.api.v1.openai_compat import router as openai_router


async def run_migrations():
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_migrations_sync)
    logger.info("Database migrations applied")


def _run_migrations_sync():
    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_command.upgrade(alembic_cfg, "head")


async def backfill_qdrant_project_ids():
    """Backfill project_id into Qdrant payloads for points that don't have one."""
    DEFAULT_PROJECT_ID = "00000000-0000-0000-0000-000000000001"
    qdrant = get_qdrant_service()

    offset = None
    updated = 0
    while True:
        result = await qdrant.client.scroll(
            collection_name=qdrant.collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
        )
        points, next_offset = result

        ids_to_update = [
            p.id for p in points
            if p.payload and "project_id" not in p.payload
        ]

        if ids_to_update:
            await qdrant.client.set_payload(
                collection_name=qdrant.collection_name,
                payload={"project_id": DEFAULT_PROJECT_ID},
                points=ids_to_update,
            )
            updated += len(ids_to_update)

        if next_offset is None:
            break
        offset = next_offset

    if updated:
        logger.info(f"Backfilled project_id for {updated} Qdrant points")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Canon Builder API")

    await run_migrations()

    qdrant = get_qdrant_service()
    await qdrant.ensure_collection()
    logger.info("Qdrant collection verified")

    await backfill_qdrant_project_ids()

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


# Serve frontend static files (production only)
# MUST be after all API routes — the catch-all would intercept them otherwise
frontend_dist = Path(__file__).resolve().parent.parent / "frontend_dist"
if frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="static")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = (frontend_dist / path).resolve()
        if file_path.is_file() and str(file_path).startswith(str(frontend_dist.resolve())):
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
