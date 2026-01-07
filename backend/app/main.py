"""
AetherCanon Builder - FastAPI Application
Main application entry point.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database.connection import init_db, init_chroma_collections, close_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Initializing AetherCanon Builder...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Provider: {settings.llm_provider}")

    # Initialize databases
    await init_db()
    logger.info("SQLite database initialized")

    init_chroma_collections()
    logger.info("ChromaDB collections initialized")

    yield

    # Shutdown
    logger.info("Shutting down AetherCanon Builder...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="AetherCanon Builder",
    description="Open-source knowledge coherence system for worldbuilders",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AetherCanon Builder API",
        "version": "0.1.0",
        "description": "Knowledge coherence system for worldbuilders",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include API routes
from .api.routes import documents, query, conflicts, review, export

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(conflicts.router, prefix="/api/conflicts", tags=["conflicts"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
