"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import auth, documents, query, proposals, graph, consistency

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(query.router, prefix="/query", tags=["Query & Retrieval"])
api_router.include_router(proposals.router, prefix="/proposals", tags=["Proposals"])
api_router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
api_router.include_router(consistency.router, prefix="/consistency", tags=["Consistency"])
