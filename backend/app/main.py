"""
Canon Builder - Main FastAPI Application
A RAG-based system for building and maintaining logically coherent knowledge systems.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.api.v1 import api_router

# Initialize FastAPI app
app = FastAPI(
    title="Canon Builder API",
    description="Open-source tool for constructing and maintaining logically coherent knowledge systems",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Canon Builder API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Qdrant URL: {settings.QDRANT_URL}")
    logger.info(f"Neo4j URI: {settings.NEO4J_URI}")
    logger.info(f"Ollama URL: {settings.OLLAMA_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Canon Builder API...")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Canon Builder API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "services": {
                "qdrant": settings.QDRANT_URL,
                "neo4j": settings.NEO4J_URI,
                "ollama": settings.OLLAMA_URL,
                "postgres": settings.POSTGRES_URL.split("@")[-1] if settings.POSTGRES_URL else None,
            },
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )
