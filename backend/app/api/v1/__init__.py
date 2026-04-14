from fastapi import APIRouter

from app.api.v1.contradictions import router as contradictions_router
from app.api.v1.documents import router as documents_router
from app.api.v1.projects import router as projects_router
from app.api.v1.query import router as query_router
from app.api.v1.settings import router as settings_router
from app.api.v1.synthesis import router as synthesis_router

router = APIRouter(prefix="/api/v1")
router.include_router(contradictions_router)
router.include_router(documents_router)
router.include_router(projects_router)
router.include_router(query_router)
router.include_router(settings_router)
router.include_router(synthesis_router)
