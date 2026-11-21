"""Health endpoint for the Fiverr Automation Agent API.

Consumes :class:`app.services.llm_service.LLMService`.
Produces: GET /api/health returning API status and NVIDIA health.
"""

from fastapi import APIRouter

from app.services.llm_service import LLMService

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    """Return the API status together with NVIDIA reachability."""
    llm = LLMService()
    llm_ok = await llm.health_check()
    return {
        "status": "ok" if llm_ok else "degraded",
        "nvidia": llm_ok,
    }